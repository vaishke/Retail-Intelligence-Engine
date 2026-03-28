import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { mockProducts, storage } from '../utils/mockData';
import { Trash2, Plus, Minus, ShoppingBag, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

export function CartPage() {
  const [cart, setCart] = useState(storage.getCart());
  const navigate = useNavigate();

  const cartItems = cart.map(item => {
    const product = mockProducts.find(p => p.id === item.productId);
    return { ...item, product };
  }).filter(item => item.product);

  const updateQuantity = (productId: string, newQuantity: number) => {
    const product = mockProducts.find(p => p.id === productId);
    if (!product) return;

    if (newQuantity <= 0) {
      removeItem(productId);
      return;
    }

    if (newQuantity > product.stock) {
      toast.error('Cannot add more than available stock');
      return;
    }

    const updatedCart = cart.map(item =>
      item.productId === productId ? { ...item, quantity: newQuantity } : item
    );
    setCart(updatedCart);
    storage.setCart(updatedCart);
  };

  const removeItem = (productId: string) => {
    const updatedCart = cart.filter(item => item.productId !== productId);
    setCart(updatedCart);
    storage.setCart(updatedCart);
    toast.success('Item removed from cart');
  };

  const availableItems = cartItems.filter(item => item.product && item.product.stock > 0);
  const unavailableItems = cartItems.filter(item => item.product && item.product.stock === 0);

  const subtotal = availableItems.reduce(
    (sum, item) => sum + (item.product?.price || 0) * item.quantity,
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
              <div className="space-y-3 md:space-y-4">
                {availableItems.map(item => (
                  <Card key={item.productId}>
                    <CardContent className="p-3 md:p-4">
                      <div className="flex gap-3 md:gap-4">
                        <img
                          src={item.product?.image}
                          alt={item.product?.name}
                          className="w-20 h-20 md:w-24 md:h-24 object-cover rounded-lg"
                        />
                        <div className="flex-1 min-w-0">
                          <Link to={`/product/${item.productId}`}>
                            <h3 className="font-semibold text-sm md:text-base hover:text-primary truncate">
                              {item.product?.name}
                            </h3>
                          </Link>
                          <p className="text-xs md:text-sm text-muted-foreground mb-2">
                            {item.product?.category}
                          </p>
                          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                            <p className="text-lg md:text-xl font-bold">
                              ${item.product?.price}
                            </p>
                            <div className="flex items-center space-x-2 sm:space-x-4">
                              <div className="flex items-center border rounded-lg">
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-7 w-7 md:h-8 md:w-8"
                                  onClick={() => updateQuantity(item.productId, item.quantity - 1)}
                                >
                                  <Minus className="h-3 w-3 md:h-4 md:w-4" />
                                </Button>
                                <span className="w-8 md:w-12 text-center text-sm md:text-base">{item.quantity}</span>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-7 w-7 md:h-8 md:w-8"
                                  onClick={() => updateQuantity(item.productId, item.quantity + 1)}
                                >
                                  <Plus className="h-3 w-3 md:h-4 md:w-4" />
                                </Button>
                              </div>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-7 w-7 md:h-8 md:w-8"
                                onClick={() => removeItem(item.productId)}
                              >
                                <Trash2 className="h-3 w-3 md:h-4 md:w-4" />
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
              <div className="flex items-center space-x-2 mb-4">
                <AlertCircle className="h-4 w-4 md:h-5 md:w-5 text-destructive" />
                <h2 className="text-xl md:text-2xl font-semibold">Unavailable Items</h2>
              </div>
              <div className="space-y-3 md:space-y-4">
                {unavailableItems.map(item => (
                  <Card key={item.productId} className="opacity-60">
                    <CardContent className="p-3 md:p-4">
                      <div className="flex gap-3 md:gap-4">
                        <img
                          src={item.product?.image}
                          alt={item.product?.name}
                          className="w-20 h-20 md:w-24 md:h-24 object-cover rounded-lg grayscale"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between">
                            <div>
                              <h3 className="font-semibold text-sm md:text-base truncate">{item.product?.name}</h3>
                              <Badge variant="destructive" className="mt-1 text-xs">
                                Out of Stock
                              </Badge>
                            </div>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 md:h-8 md:w-8 flex-shrink-0"
                              onClick={() => removeItem(item.productId)}
                            >
                              <Trash2 className="h-3 w-3 md:h-4 md:w-4" />
                            </Button>
                          </div>
                        </div>
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
          <Card className="sticky top-20">
            <CardContent className="p-4 md:p-6">
              <h2 className="text-xl md:text-2xl font-bold mb-4 md:mb-6">Order Summary</h2>
              <div className="space-y-2 md:space-y-3 mb-4 md:mb-6">
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
                {subtotal < 75 && subtotal > 0 && (
                  <p className="text-xs md:text-sm text-muted-foreground">
                    Add ${(75 - subtotal).toFixed(2)} more for free shipping!
                  </p>
                )}
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
                className="w-full text-sm md:text-base"
                size="lg"
                disabled={availableItems.length === 0}
                onClick={() => navigate('/checkout')}
              >
                Proceed to Checkout
              </Button>
              <Link to="/products">
                <Button variant="outline" className="w-full mt-3 text-sm md:text-base">
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