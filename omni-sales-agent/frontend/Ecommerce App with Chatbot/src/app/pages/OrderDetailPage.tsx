import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, CheckCircle, ExternalLink, Package, Truck } from 'lucide-react';

import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { fetchOrders, fetchProducts } from '../../services/api';
import { toast } from 'sonner';

const formatINR = (value: number) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value || 0);

export function OrderDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState<any | null>(null);
  const [products, setProducts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadOrder = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      try {
        const [ordersData, productsData] = await Promise.all([
          fetchOrders(),
          fetchProducts(),
        ]);

        setProducts(productsData.products || productsData);
        setOrder((ordersData || []).find((entry: any) => entry.id === id) || null);
      } catch (err: any) {
        toast.error(err?.message || 'Failed to load order details');
      } finally {
        setIsLoading(false);
      }
    };

    loadOrder();
  }, [id, navigate]);

  const getProduct = (productId: string) =>
    products.find((product: any) => (product._id || product.id) === productId);

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

  if (isLoading) {
    return <div className="container mx-auto px-4 py-12 text-center">Loading order details...</div>;
  }

  if (!order) {
    return (
      <div className="container mx-auto px-4 py-12 text-center">
        <h2 className="text-2xl font-bold mb-4">Order not found</h2>
        <Button onClick={() => navigate('/orders')}>Back to Orders</Button>
      </div>
    );
  }

  const deliveryStatus = order.delivery_status || order.status || 'processing';

  return (
    <div className="container mx-auto px-4 py-8">
      <Button variant="ghost" className="mb-6" onClick={() => navigate(-1)}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back
      </Button>

      <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
        <Card>
          <CardHeader>
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <CardTitle className="text-2xl">Order #{order.id}</CardTitle>
                <p className="text-sm text-muted-foreground mt-2">
                  Placed on {order.created_at ? new Date(order.created_at).toLocaleString() : 'N/A'}
                </p>
                {order.confirmed_at && (
                  <p className="text-sm text-muted-foreground">
                    Confirmed on {new Date(order.confirmed_at).toLocaleString()}
                  </p>
                )}
              </div>

              <Badge variant="secondary" className="flex items-center gap-2 px-3 py-1">
                {getStatusIcon(deliveryStatus)}
                <span className="capitalize">{deliveryStatus}</span>
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="space-y-6">
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Items in this order</h3>
              {order.items.map((item: any) => {
                const product = getProduct(item.product_id);
                const image = product?.image || product?.images?.[0] || '/fallback.png';

                return (
                  <div
                    key={item.product_id}
                    className="flex flex-col gap-4 rounded-xl border border-border/70 p-4 sm:flex-row sm:items-center"
                  >
                    <img
                      src={image}
                      alt={product?.name || 'Product'}
                      className="h-24 w-24 rounded-xl object-cover"
                    />

                    <div className="flex-1">
                      <p className="font-semibold">{product?.name || item.product_id}</p>
                      <p className="text-sm text-muted-foreground">
                        {product?.category || 'Product'}{product?.subcategory ? ` • ${product.subcategory}` : ''}
                      </p>
                      <p className="text-sm text-muted-foreground mt-1">
                        Quantity: {item.qty} x {formatINR(item.price)}
                      </p>
                    </div>

                    <p className="text-lg font-semibold">{formatINR(item.qty * item.price)}</p>
                  </div>
                );
              })}
            </div>

            <div className="rounded-xl border border-border/70 p-4 space-y-3">
              <h3 className="text-lg font-semibold">Payment & fulfillment</h3>

              <div className="flex justify-between gap-4 text-sm">
                <span className="text-muted-foreground">Payment status</span>
                <span className="capitalize">{order.payment?.status || 'N/A'}</span>
              </div>
              <div className="flex justify-between gap-4 text-sm">
                <span className="text-muted-foreground">Payment method</span>
                <span>{order.payment?.method || 'N/A'}</span>
              </div>
              <div className="flex justify-between gap-4 text-sm">
                <span className="text-muted-foreground">Transaction ID</span>
                <span className="font-mono text-right">{order.payment?.transaction_id || 'N/A'}</span>
              </div>
              <div className="flex justify-between gap-4 text-sm">
                <span className="text-muted-foreground">Fulfillment type</span>
                <span>{order.fulfillment?.type || 'N/A'}</span>
              </div>
              <div className="flex justify-between gap-4 text-sm">
                <span className="text-muted-foreground">Fulfillment status</span>
                <span>{order.fulfillment?.status || 'N/A'}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Order total</span>
                <span className="font-semibold">{formatINR(order.final_price || 0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Discounts applied</span>
                <span>{order.discounts_applied?.length || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Bonus points</span>
                <span>{order.loyalty_bonus_points ?? 0}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Tracking details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between gap-4 text-sm">
                <span className="text-muted-foreground">Shipment ID</span>
                <span className="font-mono text-right">{order.shipment_id || 'N/A'}</span>
              </div>
              <div className="flex justify-between gap-4 text-sm">
                <span className="text-muted-foreground">Invoice ID</span>
                <span className="font-mono text-right">{order.invoice_id || 'N/A'}</span>
              </div>
              <div className="flex justify-between gap-4 text-sm">
                <span className="text-muted-foreground">Tracking Number</span>
                <span className="font-mono text-right">{order.tracking_number || 'N/A'}</span>
              </div>

              {order.tracking_number && (
                <Button
                  variant="outline"
                  className="w-full mt-2"
                  onClick={() => window.open(`/order/${order.id}`, '_blank', 'noopener,noreferrer')}
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Open In New Tab
                </Button>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
