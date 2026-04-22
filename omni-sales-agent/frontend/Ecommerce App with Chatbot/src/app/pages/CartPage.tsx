import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { fetchCart, fetchProducts, addToCart } from '../../services/api';
import { Trash2, Plus, Minus, ShoppingBag } from 'lucide-react';
import { toast } from 'sonner';

const formatINR = (value: number) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);

export function CartPage() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const userId = user.user_id || user.id;

  const [cart, setCart] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    if (!userId) {
      setCart([]);
      return;
    }

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
    const product = products.find((p: any) => (p._id || p.id) === (item.product_id || item.productId));
    const quantity = item.quantity || item.qty || 1;
    const totalStock = (product?.available_stores || []).reduce(
      (sum: number, store: any) => sum + (store.stock || 0),
      0
    );

    return {
      ...item,
      quantity,
      product: product
        ? {
            ...product,
            imageUrl: product.image || product.images?.[0] || '',
            totalStock,
          }
        : null,
    };
  }).filter(item => item.product);

  const updateQuantity = async (productId: string, newQuantity: number) => {
    if (!userId) {
      toast.error("Please log in to update your cart");
      return;
    }

    if (newQuantity <= 0) {
      removeItem(productId);
      return;
    }

    try {
      await addToCart(userId, productId, newQuantity);
      window.dispatchEvent(new Event("storage"));
      await loadData();
    } catch {
      toast.error("Failed to update cart");
    }
  };

  const removeItem = async (productId: string) => {
    if (!userId) {
      toast.error("Please log in to update your cart");
      return;
    }

    try {
      await addToCart(userId, productId, 0);
      window.dispatchEvent(new Event("storage"));
      await loadData();
      toast.success('Item removed from cart');
    } catch {
      toast.error("Failed to remove item");
    }
  };

  const availableItems = cartItems.filter(item => item.product?.totalStock > 0);
  const unavailableItems = cartItems.filter(item => item.product?.totalStock <= 0);

  const subtotal = availableItems.reduce(
    (sum, item) => sum + item.product.price * item.quantity,
    0
  );

  const shipping = subtotal > 999 ? 0 : 99;
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

              <div className="grid gap-4">
                {availableItems.map(item => (
                  <Card key={item.product_id || item.productId} className="overflow-hidden border-border/70">
                    <CardContent className="p-4">
                      <div className="flex flex-col gap-4 sm:flex-row">
                        <img
                          src={item.product.imageUrl}
                          alt={item.product.name}
                          className="h-32 w-full rounded-xl object-cover sm:h-28 sm:w-28"
                        />

                        <div className="flex-1 space-y-3">
                          <Link to={`/product/${item.product_id || item.productId}`}>
                            <h3 className="text-lg font-semibold hover:text-primary">
                              {item.product.name}
                            </h3>
                          </Link>

                          <div className="flex flex-wrap gap-2">
                            <Badge variant="secondary">{item.product.category}</Badge>
                            {item.product.subcategory && (
                              <Badge variant="outline">{item.product.subcategory}</Badge>
                            )}
                            <Badge variant="outline" className="text-green-700 border-green-200 bg-green-50">
                              {item.product.totalStock} in stock
                            </Badge>
                          </div>

                          <p className="text-sm text-muted-foreground">
                            {item.product.description}
                          </p>

                          <div className="flex flex-col gap-3 pt-1 sm:flex-row sm:items-center sm:justify-between">
                            <div>
                              <p className="text-xl font-bold">
                                {formatINR(item.product.price)}
                              </p>
                              <p className="text-sm text-muted-foreground">
                                Item total: {formatINR(item.product.price * item.quantity)}
                              </p>
                            </div>

                            <div className="flex items-center justify-between gap-3 sm:justify-end">
                              <div className="flex items-center rounded-lg border bg-background">
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() =>
                                    updateQuantity(item.product_id || item.productId, item.quantity - 1)
                                  }
                                >
                                  <Minus className="h-4 w-4" />
                                </Button>

                                <span className="min-w-10 px-3 text-center font-medium">{item.quantity}</span>

                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() =>
                                    updateQuantity(item.product_id || item.productId, item.quantity + 1)
                                  }
                                >
                                  <Plus className="h-4 w-4" />
                                </Button>
                              </div>

                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => removeItem(item.product_id || item.productId)}
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
              <h2 className="mb-4 text-xl font-semibold text-red-500">
                Unavailable Items
              </h2>

              <div className="grid gap-3">
                {unavailableItems.map(item => (
                  <Card key={item.product_id || item.productId} className="border-red-200 bg-red-50/40">
                    <CardContent className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
                      <div className="flex items-center gap-4">
                        <img
                          src={item.product.imageUrl}
                          alt={item.product.name}
                          className="h-20 w-20 rounded-xl object-cover"
                        />
                        <div>
                          <p className="font-semibold">{item.product.name}</p>
                          <p className="text-sm text-muted-foreground">{item.product.category}</p>
                          <Badge variant="destructive" className="mt-2">Out of Stock</Badge>
                        </div>
                      </div>

                      <div className="flex items-center justify-between gap-3 sm:justify-end">
                        <p className="font-semibold">{formatINR(item.product.price)}</p>
                        <Button onClick={() => removeItem(item.product_id || item.productId)}>
                          Remove
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

        </div>

        {/* Order Summary */}
        <div>
          <Card className="sticky top-20 overflow-hidden">
            <CardContent className="p-6">
              <h2 className="text-2xl font-bold mb-4">Order Summary</h2>

              <div className="space-y-3 mb-6">
                <div className="flex justify-between">
                  <span>Subtotal</span>
                  <span>{formatINR(subtotal)}</span>
                </div>

                <div className="flex justify-between">
                  <span>Shipping</span>
                  <span>{shipping === 0 ? 'FREE' : formatINR(shipping)}</span>
                </div>

                <div className="border-t pt-3 flex justify-between font-bold text-lg">
                  <span>Total</span>
                  <span>{formatINR(total)}</span>
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
