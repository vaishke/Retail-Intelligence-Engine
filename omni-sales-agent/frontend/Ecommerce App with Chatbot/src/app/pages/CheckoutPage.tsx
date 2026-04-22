import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { CreditCard, Banknote, QrCode, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';

import { fetchCart, fetchProducts, placeOrder } from '../../services/api';

export function CheckoutPage() {
  const [paymentMethod, setPaymentMethod] = useState('card');
  const [isProcessing, setIsProcessing] = useState(false);
  const [orderComplete, setOrderComplete] = useState(false);
  const [orderId, setOrderId] = useState('');
  const [cartItems, setCartItems] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);

  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const userId = user.user_id || user.id;

  useEffect(() => {
    loadData();

    const syncCheckoutCart = () => {
      loadData();
    };

    window.addEventListener("storage", syncCheckoutCart);
    window.addEventListener("focus", syncCheckoutCart);

    return () => {
      window.removeEventListener("storage", syncCheckoutCart);
      window.removeEventListener("focus", syncCheckoutCart);
    };
  }, []);

  const loadData = async () => {
    if (!userId) {
      setCartItems([]);
      return;
    }

    const cartData = await fetchCart(userId);
    const productsData = await fetchProducts();

    setProducts(productsData.products || productsData);

    const cartItemsData = cartData.cart || cartData;
    const merged = cartItemsData.map((item: any) => {
      const product = (productsData.products || productsData).find((p: any) => (p._id || p.id) === item.product_id);
      return {
        ...item,
        product,
      };
    });

    setCartItems(merged);
  };

  const subtotal = cartItems.reduce(
    (sum, item) => sum + (item.product?.price || 0) * item.quantity,
    0
  );

  const shipping = subtotal > 75 ? 0 : 15;
  const total = subtotal + shipping;

  const handlePlaceOrder = async () => {
    if (!userId) {
      toast.error('Please log in to place an order');
      return;
    }

    setIsProcessing(true);

    try {
      const payload = {
        user_id: userId,
        items: cartItems.map(item => ({
          product_id: item.product_id,
          quantity: item.quantity,
          price: item.product?.price || 0,
        })),
        total,
        payment_method: paymentMethod,
      };

      const res = await placeOrder(payload);

      setOrderId(res.order_id || `ORD-${Date.now()}`);
      setOrderComplete(true);
      window.dispatchEvent(new Event("storage"));

      toast.success('Order placed successfully!');
    } catch (err: any) {
      toast.error(err?.message || 'Failed to place order');
    } finally {
      setIsProcessing(false);
    }
  };

  if (orderComplete) {
    return (
      <div className="container mx-auto px-4 py-8 md:py-12">
        <Card className="max-w-2xl mx-auto text-center">
          <CardContent className="p-8 md:p-12">
            <CheckCircle2 className="h-20 w-20 text-green-500 mx-auto mb-4" />
            <h1 className="text-3xl font-bold mb-4">Order Confirmed!</h1>

            <div className="bg-muted p-4 rounded-lg mb-4">
              <p className="text-sm text-muted-foreground">Order ID</p>
              <p className="text-xl font-bold">{orderId}</p>
            </div>

            <Button onClick={() => navigate('/products')}>
              Continue Shopping
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6 md:py-8">
      <h1 className="text-3xl font-bold mb-6">Checkout</h1>

      <div className="grid lg:grid-cols-3 gap-6">
        
        {/* LEFT SIDE */}
        <div className="lg:col-span-2 space-y-6">

          {/* Shipping */}
          <Card>
            <CardHeader>
              <CardTitle>Shipping Address</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input placeholder="First Name" />
              <Input placeholder="Last Name" />
              <Input placeholder="Address" />
              <Input placeholder="City" />
              <Input placeholder="State" />
              <Input placeholder="ZIP Code" />
            </CardContent>
          </Card>

          {/* Payment */}
          <Card>
            <CardHeader>
              <CardTitle>Payment Method</CardTitle>
            </CardHeader>
            <CardContent>
              <RadioGroup value={paymentMethod} onValueChange={setPaymentMethod}>
                
                <div className="flex items-center space-x-3 border p-3 rounded">
                  <RadioGroupItem value="card" id="card" />
                  <Label htmlFor="card" className="flex items-center">
                    <CreditCard className="mr-2 h-4 w-4" />
                    Card
                  </Label>
                </div>

                <div className="flex items-center space-x-3 border p-3 rounded">
                  <RadioGroupItem value="upi" id="upi" />
                  <Label htmlFor="upi" className="flex items-center">
                    <QrCode className="mr-2 h-4 w-4" />
                    UPI
                  </Label>
                </div>

                <div className="flex items-center space-x-3 border p-3 rounded">
                  <RadioGroupItem value="cod" id="cod" />
                  <Label htmlFor="cod" className="flex items-center">
                    <Banknote className="mr-2 h-4 w-4" />
                    Cash on Delivery
                  </Label>
                </div>

              </RadioGroup>
            </CardContent>
          </Card>

        </div>

        {/* RIGHT SIDE */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Order Summary</CardTitle>
            </CardHeader>

            <CardContent>
              <div className="space-y-3 mb-4">
                {cartItems.map(item => (
                  <div key={item.product_id} className="flex justify-between">
                    <span>{item.product?.name} × {item.quantity}</span>
                    <span>
                      ${(item.product?.price * item.quantity).toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>

              <div className="border-t pt-3 space-y-2">
                <div className="flex justify-between">
                  <span>Subtotal</span>
                  <span>${subtotal.toFixed(2)}</span>
                </div>

                <div className="flex justify-between">
                  <span>Shipping</span>
                  <span>{shipping === 0 ? 'FREE' : `$${shipping}`}</span>
                </div>

                <div className="flex justify-between font-bold text-lg">
                  <span>Total</span>
                  <span>${total.toFixed(2)}</span>
                </div>
              </div>

              <Button
                className="w-full mt-4"
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
