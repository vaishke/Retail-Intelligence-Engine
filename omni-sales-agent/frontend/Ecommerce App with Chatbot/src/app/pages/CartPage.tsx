import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { fetchCart, fetchProducts, addToCart } from '../../services/api';
import { Trash2, Plus, Minus, ShoppingBag, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

export function CartPage() {
  const navigate = useNavigate();
  const userId = "1"; // later replace with real auth

  const [cart, setCart] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const cartRes = await fetchCart(userId);
      const productRes = await fetchProducts();

      setCart(cartRes.cart || []);
      setProducts(productRes.products || productRes);
    } catch (err) {
      toast.error("Failed to load cart");
    }
  };

  const cartItems = cart.map(item => {
    const product = products.find(p => p.id === item.productId);
    return { ...item, product };
  }).filter(item => item.product);

  const updateQuantity = async (productId: string, newQuantity: number) => {
    if (newQuantity <= 0) {
      removeItem(productId);
      return;
    }

    try {
      await addToCart(userId, productId, newQuantity);
      await loadData();
    } catch {
      toast.error("Failed to update cart");
    }
  };

  const removeItem = async (productId: string) => {
    try {
      await addToCart(userId, productId, 0); // assuming backend handles remove
      await loadData();
      toast.success('Item removed from cart');
    } catch {
      toast.error("Failed to remove item");
    }
  };

  const availableItems = cartItems.filter(item => item.product?.stock > 0);
  const unavailableItems = cartItems.filter(item => item.product?.stock === 0);

  const subtotal = availableItems.reduce(
    (sum, item) => sum + item.product.price * item.quantity,
    0
  );

  const shipping = subtotal > 75 ? 0 : 15;
  const total = subtotal + shipping;

  if (cartItems.length === 0) {
    return (
      <div className="container mx-auto px-4 py-12 text-center">
        <ShoppingBag className="h-24 w-24 mx-auto mb-4 text-muted-foreground" />
        <h2 className="text-3xl font-bold mb-4">Your cart is empty</h2>
        <p className="text-muted-foreground mb-6">
          Add some products to get started!
        </p>
        <Link to="/products">
          <Button size="lg">Continue Shopping</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6 md:py-8">
      <h1 className="text-3xl md:text-4xl font-bold mb-6 md:mb-8">Shopping Cart</h1>

      <div className="grid lg:grid-cols-3 gap-6 md:gap-8">
        <div className="lg:col-span-2">

          {/* Available Items */}
          {availableItems.length > 0 && (
            <div className="mb-6">
              <h2 className="text-xl md:text-2xl font-semibold mb-4">Available Items</h2>

              <div className="space-y-4">
                {availableItems.map(item => (
                  <Card key={item.productId}>
                    <CardContent className="p-4">
                      <div className="flex gap-4">
                        <img
                          src={item.product.image}
                          alt={item.product.name}
                          className="w-24 h-24 object-cover rounded-lg"
                        />

                        <div className="flex-1">
                          <Link to={`/product/${item.productId}`}>
                            <h3 className="font-semibold hover:text-primary">
                              {item.product.name}
                            </h3>
                          </Link>

                          <p className="text-sm text-muted-foreground mb-2">
                            {item.product.category}
                          </p>

                          <div className="flex justify-between items-center">
                            <p className="text-xl font-bold">
                              ${item.product.price}
                            </p>

                            <div className="flex items-center space-x-3">
                              <div className="flex items-center border rounded-lg">
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() =>
                                    updateQuantity(item.productId, item.quantity - 1)
                                  }
                                >
                                  <Minus className="h-4 w-4" />
                                </Button>

                                <span className="px-3">{item.quantity}</span>

                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() =>
                                    updateQuantity(item.productId, item.quantity + 1)
                                  }
                                >
                                  <Plus className="h-4 w-4" />
                                </Button>
                              </div>

                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => removeItem(item.productId)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>

                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Unavailable Items */}
          {unavailableItems.length > 0 && (
            <div>
              <h2 className="text-xl font-semibold mb-4 text-red-500">
                Unavailable Items
              </h2>

              {unavailableItems.map(item => (
                <Card key={item.productId} className="opacity-60 mb-3">
                  <CardContent className="p-4 flex justify-between items-center">
                    <div>
                      <p>{item.product.name}</p>
                      <Badge variant="destructive">Out of Stock</Badge>
                    </div>

                    <Button onClick={() => removeItem(item.productId)}>
                      Remove
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

        </div>

        {/* Order Summary */}
        <div>
          <Card className="sticky top-20">
            <CardContent className="p-6">
              <h2 className="text-2xl font-bold mb-4">Order Summary</h2>

              <div className="space-y-3 mb-6">
                <div className="flex justify-between">
                  <span>Subtotal</span>
                  <span>${subtotal.toFixed(2)}</span>
                </div>

                <div className="flex justify-between">
                  <span>Shipping</span>
                  <span>{shipping === 0 ? 'FREE' : `$${shipping}`}</span>
                </div>

                <div className="border-t pt-3 flex justify-between font-bold text-lg">
                  <span>Total</span>
                  <span>${total.toFixed(2)}</span>
                </div>
              </div>

              <Button
                className="w-full"
                disabled={availableItems.length === 0}
                onClick={() => navigate('/checkout')}
              >
                Proceed to Checkout
              </Button>

              <Link to="/products">
                <Button variant="outline" className="w-full mt-3">
                  Continue Shopping
                </Button>
              </Link>

            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  );
}