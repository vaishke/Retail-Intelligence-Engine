import { useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent } from '../components/ui/card';
import { fetchProducts, addToCart } from '../../services/api';
import { ShoppingCart, Star, Minus, Plus, ArrowLeft, Package, Truck } from 'lucide-react';
import { toast } from 'sonner';

export function ProductDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [product, setProduct] = useState<any>(null); // ✅ from API
  const [quantity, setQuantity] = useState(1);

  // ✅ FETCH PRODUCT FROM BACKEND
  useEffect(() => {
    fetchProducts().then((data) => {
      const found = data.find((p: any) => p._id === id || p.id === id);
      setProduct(found);
    });
  }, [id]);

  if (!product) {
    return (
      <div className="container mx-auto px-4 py-12 text-center">
        <h2 className="text-2xl font-bold mb-4">Product Not Found</h2>
        <Button onClick={() => navigate('/')}>Go Home</Button>
      </div>
    );
  }

  // ✅ UPDATED ADD TO CART (API)
  const handleAddToCart = async () => {
    if (product.stock === 0) {
      toast.error('Product is out of stock');
      return;
    }

    const user = JSON.parse(localStorage.getItem("user") || "{}");
    const userId = user.user_id || user.id;

    if (!userId) {
      toast.error("Please log in to add items to cart");
      return;
    }

    try {
      await addToCart(userId, product._id || product.id, quantity);
      window.dispatchEvent(new Event("storage"));
      toast.success(`Added ${quantity} item(s) to cart`);
    } catch (err) {
      console.error(err);
      toast.error("Failed to add to cart");
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <Button variant="ghost" className="mb-6" onClick={() => navigate(-1)}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back
      </Button>

      <div className="grid md:grid-cols-2 gap-8">
        {/* Product Image */}
        <div className="relative">
          <img
            src={product.image}
            alt={product.name}
            className="w-full rounded-lg shadow-lg"
          />
          {product.stock === 0 && (
            <Badge className="absolute top-4 right-4" variant="destructive">
              Out of Stock
            </Badge>
          )}
        </div>

        {/* Product Info */}
        <div>
          <div className="mb-4">
            <Badge className="mb-2">{product.category}</Badge>
            <h1 className="text-4xl font-bold mb-2">{product.name}</h1>
            <div className="flex items-center space-x-2 mb-4">
              <div className="flex items-center">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    className={`h-5 w-5 ${
                      i < Math.floor(product.rating)
                        ? 'fill-yellow-400 text-yellow-400'
                        : 'text-gray-300'
                    }`}
                  />
                ))}
              </div>
              <span className="text-lg font-semibold">{product.rating}</span>
              <span className="text-muted-foreground">(128 reviews)</span>
            </div>
            <p className="text-4xl font-bold text-primary mb-6">
              ${product.price}
            </p>
          </div>

          <Card className="mb-6">
            <CardContent className="p-4">
              <h3 className="font-semibold mb-2">Description</h3>
              <p className="text-muted-foreground">{product.description}</p>
            </CardContent>
          </Card>

          {/* Stock Info */}
          <div className="flex items-center space-x-6 mb-6">
            <div className="flex items-center space-x-2">
              <Package className="h-5 w-5 text-muted-foreground" />
              <span className="text-sm">
                {product.stock > 0 ? (
                  <span className="text-green-600 font-semibold">
                    {product.stock} in stock
                  </span>
                ) : (
                  <span className="text-red-600 font-semibold">Out of stock</span>
                )}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <Truck className="h-5 w-5 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                Free shipping on orders over $75
              </span>
            </div>
          </div>

          {/* Quantity Selector */}
          {product.stock > 0 && (
            <>
              <div className="flex items-center space-x-4 mb-6">
                <span className="font-semibold">Quantity:</span>
                <div className="flex items-center border rounded-lg">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  >
                    <Minus className="h-4 w-4" />
                  </Button>
                  <span className="w-12 text-center font-semibold">{quantity}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setQuantity(Math.min(product.stock ?? quantity + 1, quantity + 1))}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* Buttons */}
              <div className="flex space-x-4">
                <Button className="flex-1" size="lg" onClick={handleAddToCart}>
                  <ShoppingCart className="h-5 w-5 mr-2" />
                  Add to Cart
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  onClick={async () => {
                    await handleAddToCart();
                    navigate('/cart');
                  }}
                >
                  Buy Now
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
