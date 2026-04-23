import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { fetchOrders, fetchProducts } from '../../services/api';
import { Package, Truck, CheckCircle, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';

const formatINR = (value: number) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);

export function OrdersPage() {
  const [orders, setOrders] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const loadOrders = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        navigate("/login");
        return;
      }

      try {
        const [ordersData, productsData] = await Promise.all([
          fetchOrders(),
          fetchProducts(),
        ]);
        setOrders(ordersData);
        setProducts(productsData.products || productsData);
      } catch (err: any) {
        toast.error(err?.message || "Failed to load orders");
      } finally {
        setIsLoading(false);
      }
    };

    loadOrders();
  }, [navigate]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'confirmed':
      case 'fulfilled':
        return <Package className="h-5 w-5" />;
      case 'shipped':
      case 'processing':
        return <Truck className="h-5 w-5" />;
      case 'delivered':
        return <CheckCircle className="h-5 w-5" />;
      default:
        return <Package className="h-5 w-5" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed':
      case 'fulfilled':
        return 'default';
      case 'shipped':
      case 'processing':
        return 'secondary';
      case 'delivered':
        return 'success' as any;
      default:
        return 'default';
    }
  };

  const getProduct = (productId: string) =>
    products.find((p: any) => (p._id || p.id) === productId);

  const openOrderInNewTab = (orderId: string) => {
    window.open(`/order/${orderId}`, '_blank', 'noopener,noreferrer');
  };

  if (isLoading) {
    return <div className="container mx-auto px-4 py-12 text-center">Loading orders...</div>;
  }

  if (orders.length === 0) {
    return (
      <div className="container mx-auto px-4 py-12 text-center">
        <Package className="h-24 w-24 mx-auto mb-4 text-muted-foreground" />
        <h2 className="text-3xl font-bold mb-4">No orders yet</h2>
        <p className="text-muted-foreground mb-6">
          Start shopping to see your orders here!
        </p>
        <Button onClick={() => navigate('/products')}>
          Browse Products
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8">My Orders</h1>

      <div className="space-y-6">
        {orders.map(order => (
          <Card key={order.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="flex items-center space-x-2">
                    <span>Order #{order.id}</span>
                  </CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">
                    Placed on {new Date(order.created_at).toLocaleDateString()}
                  </p>
                </div>
                <Badge variant={getStatusColor(order.status)} className="flex items-center space-x-1">
                  {getStatusIcon(order.delivery_status || order.status)}
                  <span className="capitalize">{order.delivery_status || order.status}</span>
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 mb-6">
                {order.items.map((item: any) => {
                  const product = getProduct(item.product_id);
                  return (
                    <div key={item.product_id} className="flex items-center space-x-4">
                      <img
                        src={product?.image || product?.images?.[0] || ''}
                        alt={product?.name || 'Product'}
                        className="w-16 h-16 object-cover rounded-lg"
                      />
                      <div className="flex-1">
                        <p className="font-semibold">{product?.name || item.product_id}</p>
                        <p className="text-sm text-muted-foreground">
                          Quantity: {item.qty} x {formatINR(item.price)}
                        </p>
                      </div>
                      <p className="font-semibold">{formatINR(item.qty * item.price)}</p>
                    </div>
                  );
                })}
              </div>

              <div className="border-t pt-4">
                <div className="flex justify-between items-center mb-4">
                  <span className="text-xl font-bold">Total</span>
                  <span className="text-2xl font-bold text-primary">
                    {formatINR(order.final_price || 0)}
                  </span>
                </div>

                {(order.shipment_id || order.invoice_id) && (
                  <div className="bg-muted p-4 rounded-lg space-y-2">
                    {order.shipment_id && (
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Shipment ID</span>
                        <span className="font-mono">{order.shipment_id}</span>
                      </div>
                    )}
                    {order.invoice_id && (
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Invoice ID</span>
                        <span className="font-mono">{order.invoice_id}</span>
                      </div>
                    )}
                    {order.tracking_number && (
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Tracking Number</span>
                        <span className="font-mono">{order.tracking_number}</span>
                      </div>
                    )}
                    {order.tracking_number && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full mt-2"
                        onClick={() => openOrderInNewTab(order.id)}
                      >
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Tracking Available
                      </Button>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
