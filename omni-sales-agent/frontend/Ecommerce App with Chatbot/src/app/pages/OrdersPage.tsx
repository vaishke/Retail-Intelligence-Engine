import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { storage, mockProducts } from '../utils/mockData';
import { Package, Truck, CheckCircle, ExternalLink } from 'lucide-react';

export function OrdersPage() {
  const orders = storage.getOrders();

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'confirmed':
        return <Package className="h-5 w-5" />;
      case 'shipped':
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
        return 'default';
      case 'shipped':
        return 'secondary';
      case 'delivered':
        return 'success' as any;
      default:
        return 'default';
    }
  };

  if (orders.length === 0) {
    return (
      <div className="container mx-auto px-4 py-12 text-center">
        <Package className="h-24 w-24 mx-auto mb-4 text-muted-foreground" />
        <h2 className="text-3xl font-bold mb-4">No orders yet</h2>
        <p className="text-muted-foreground mb-6">
          Start shopping to see your orders here!
        </p>
        <Button onClick={() => window.location.href = '/products'}>
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
                    Placed on {new Date(order.createdAt).toLocaleDateString()}
                  </p>
                </div>
                <Badge variant={getStatusColor(order.status)} className="flex items-center space-x-1">
                  {getStatusIcon(order.status)}
                  <span className="capitalize">{order.status}</span>
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 mb-6">
                {order.items.map(item => {
                  const product = mockProducts.find(p => p.id === item.productId);
                  return (
                    <div key={item.productId} className="flex items-center space-x-4">
                      <img
                        src={product?.image}
                        alt={product?.name}
                        className="w-16 h-16 object-cover rounded-lg"
                      />
                      <div className="flex-1">
                        <p className="font-semibold">{product?.name}</p>
                        <p className="text-sm text-muted-foreground">
                          Quantity: {item.quantity} × ${item.price.toFixed(2)}
                        </p>
                      </div>
                      <p className="font-semibold">${(item.quantity * item.price).toFixed(2)}</p>
                    </div>
                  );
                })}
              </div>

              <div className="border-t pt-4">
                <div className="flex justify-between items-center mb-4">
                  <span className="text-xl font-bold">Total</span>
                  <span className="text-2xl font-bold text-primary">
                    ${order.total.toFixed(2)}
                  </span>
                </div>

                {order.shipmentId && (
                  <div className="bg-muted p-4 rounded-lg space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Shipment ID</span>
                      <span className="font-mono">{order.shipmentId}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Invoice ID</span>
                      <span className="font-mono">{order.invoiceId}</span>
                    </div>
                    {order.trackingUrl && (
                      <Button variant="outline" size="sm" className="w-full mt-2">
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Track Shipment
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
