import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { mockProducts, storage, Order } from '../utils/mockData';
import { CreditCard, Banknote, QrCode, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';

export function CheckoutPage() {
  const [paymentMethod, setPaymentMethod] = useState('card');
  const [isProcessing, setIsProcessing] = useState(false);
  const [orderComplete, setOrderComplete] = useState(false);
  const [orderId, setOrderId] = useState('');
  const navigate = useNavigate();

  const cart = storage.getCart();
  const user = storage.getUser();

  if (!user) {
    navigate('/login');
    return null;
  }

  const cartItems = cart.map(item => {
    const product = mockProducts.find(p => p.id === item.productId);
    return { ...item, product };
  }).filter(item => item.product && item.product.stock > 0);

  const subtotal = cartItems.reduce(
    (sum, item) => sum + (item.product?.price || 0) * item.quantity,
    0
  );
  const shipping = subtotal > 75 ? 0 : 15;
  const total = subtotal + shipping;

  const handlePlaceOrder = () => {
    setIsProcessing(true);

    // Simulate payment processing
    setTimeout(() => {
      const newOrderId = `ORD-${Date.now()}`;
      const order: Order = {
        id: newOrderId,
        userId: user.id,
        items: cartItems.map(item => ({
          productId: item.productId,
          quantity: item.quantity,
          price: item.product?.price || 0,
        })),
        total,
        status: 'confirmed',
        createdAt: new Date().toISOString(),
        shipmentId: `SHIP-${Date.now()}`,
        invoiceId: `INV-${Date.now()}`,
        trackingUrl: `https://tracking.example.com/${newOrderId}`,
      };

      const orders = storage.getOrders();
      storage.setOrders([order, ...orders]);

      // Update inventory (mock)
      cartItems.forEach(item => {
        const product = item.product;
        if (product) {
          product.stock -= item.quantity;
        }
      });

      // Award loyalty points
      const pointsEarned = Math.floor(total);
      user.loyaltyPoints += pointsEarned;
      storage.setUser(user);

      // Clear cart
      storage.setCart([]);

      setOrderId(newOrderId);
      setOrderComplete(true);
      setIsProcessing(false);
      toast.success(`Order placed! You earned ${pointsEarned} loyalty points!`);
    }, 2000);
  };

  if (orderComplete) {
    return (
      <div className="container mx-auto px-4 py-8 md:py-12">
        <Card className="max-w-2xl mx-auto text-center">
          <CardContent className="p-8 md:p-12">
            <CheckCircle2 className="h-20 w-20 md:h-24 md:w-24 text-green-500 mx-auto mb-4 md:mb-6" />
            <h1 className="text-3xl md:text-4xl font-bold mb-3 md:mb-4">Order Confirmed!</h1>
            <p className="text-lg md:text-xl text-muted-foreground mb-4 md:mb-6">
              Thank you for your purchase!
            </p>
            <div className="bg-muted p-4 md:p-6 rounded-lg mb-4 md:mb-6">
              <p className="text-xs md:text-sm text-muted-foreground mb-2">Order ID</p>
              <p className="text-xl md:text-2xl font-bold break-all">{orderId}</p>
            </div>
            <div className="space-y-1.5 md:space-y-2 text-xs md:text-sm text-muted-foreground mb-6 md:mb-8">
              <p>✓ Order confirmation sent to {user.email}</p>
              <p>✓ Shipment ID: SHIP-{Date.now()}</p>
              <p>✓ Invoice ID: INV-{Date.now()}</p>
              <p>✓ Tracking available in 2-4 hours</p>
            </div>
            <div className="flex flex-col sm:flex-row gap-3 md:gap-4 justify-center">
              <Button onClick={() => navigate('/orders')} className="w-full sm:w-auto">
                View Orders
              </Button>
              <Button variant="outline" onClick={() => navigate('/')} className="w-full sm:w-auto">
                Continue Shopping
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6 md:py-8">
      <h1 className="text-3xl md:text-4xl font-bold mb-6 md:mb-8">Checkout</h1>

      <div className="grid lg:grid-cols-3 gap-6 md:gap-8">
        <div className="lg:col-span-2 space-y-4 md:space-y-6">
          {/* Shipping Address */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg md:text-xl">Shipping Address</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 md:space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
                <div>
                  <Label htmlFor="firstName" className="text-sm">First Name</Label>
                  <Input id="firstName" placeholder="John" required className="text-sm md:text-base" />
                </div>
                <div>
                  <Label htmlFor="lastName" className="text-sm">Last Name</Label>
                  <Input id="lastName" placeholder="Doe" required className="text-sm md:text-base" />
                </div>
              </div>
              <div>
                <Label htmlFor="address" className="text-sm">Address</Label>
                <Input id="address" placeholder="123 Main St" required className="text-sm md:text-base" />
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 md:gap-4">
                <div>
                  <Label htmlFor="city" className="text-sm">City</Label>
                  <Input id="city" placeholder="New York" required className="text-sm md:text-base" />
                </div>
                <div>
                  <Label htmlFor="state" className="text-sm">State</Label>
                  <Input id="state" placeholder="NY" required className="text-sm md:text-base" />
                </div>
                <div className="col-span-2 md:col-span-1">
                  <Label htmlFor="zip" className="text-sm">ZIP Code</Label>
                  <Input id="zip" placeholder="10001" required className="text-sm md:text-base" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Payment Method */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg md:text-xl">Payment Method</CardTitle>
            </CardHeader>
            <CardContent>
              <RadioGroup value={paymentMethod} onValueChange={setPaymentMethod}>
                <div className="flex items-center space-x-3 p-3 md:p-4 border rounded-lg cursor-pointer hover:bg-muted">
                  <RadioGroupItem value="card" id="card" />
                  <Label htmlFor="card" className="flex items-center cursor-pointer flex-1 text-sm md:text-base">
                    <CreditCard className="h-4 w-4 md:h-5 md:w-5 mr-2 md:mr-3" />
                    Credit / Debit Card
                  </Label>
                </div>
                <div className="flex items-center space-x-3 p-3 md:p-4 border rounded-lg cursor-pointer hover:bg-muted">
                  <RadioGroupItem value="upi" id="upi" />
                  <Label htmlFor="upi" className="flex items-center cursor-pointer flex-1 text-sm md:text-base">
                    <QrCode className="h-4 w-4 md:h-5 md:w-5 mr-2 md:mr-3" />
                    UPI / QR Code
                  </Label>
                </div>
                <div className="flex items-center space-x-3 p-3 md:p-4 border rounded-lg cursor-pointer hover:bg-muted">
                  <RadioGroupItem value="cod" id="cod" />
                  <Label htmlFor="cod" className="flex items-center cursor-pointer flex-1 text-sm md:text-base">
                    <Banknote className="h-4 w-4 md:h-5 md:w-5 mr-2 md:mr-3" />
                    Cash on Delivery
                  </Label>
                </div>
              </RadioGroup>

              {paymentMethod === 'card' && (
                <div className="mt-4 space-y-3 md:space-y-4">
                  <div>
                    <Label htmlFor="cardNumber" className="text-sm">Card Number</Label>
                    <Input id="cardNumber" placeholder="1234 5678 9012 3456" className="text-sm md:text-base" />
                  </div>
                  <div className="grid grid-cols-2 gap-3 md:gap-4">
                    <div>
                      <Label htmlFor="expiry" className="text-sm">Expiry Date</Label>
                      <Input id="expiry" placeholder="MM/YY" className="text-sm md:text-base" />
                    </div>
                    <div>
                      <Label htmlFor="cvv" className="text-sm">CVV</Label>
                      <Input id="cvv" placeholder="123" type="password" className="text-sm md:text-base" />
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Order Summary */}
        <div>
          <Card className="lg:sticky lg:top-20">
            <CardHeader>
              <CardTitle className="text-lg md:text-xl">Order Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 md:space-y-4 mb-4 md:mb-6">
                {cartItems.map(item => (
                  <div key={item.productId} className="flex justify-between text-xs md:text-sm">
                    <span className="truncate mr-2">
                      {item.product?.name} × {item.quantity}
                    </span>
                    <span className="font-semibold flex-shrink-0">
                      ${((item.product?.price || 0) * item.quantity).toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
              <div className="space-y-2 md:space-y-3 border-t pt-3 md:pt-4">
                <div className="flex justify-between text-sm md:text-base">
                  <span className="text-muted-foreground">Subtotal</span>
                  <span className="font-semibold">${subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm md:text-base">
                  <span className="text-muted-foreground">Shipping</span>
                  <span className="font-semibold">
                    {shipping === 0 ? 'FREE' : `$${shipping.toFixed(2)}`}
                  </span>
                </div>
                <div className="border-t pt-2 md:pt-3">
                  <div className="flex justify-between items-center">
                    <span className="text-lg md:text-xl font-bold">Total</span>
                    <span className="text-xl md:text-2xl font-bold text-primary">
                      ${total.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
              <Button
                className="w-full mt-4 md:mt-6 text-sm md:text-base"
                size="lg"
                onClick={handlePlaceOrder}
                disabled={isProcessing}
              >
                {isProcessing ? 'Processing...' : 'Place Order'}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}