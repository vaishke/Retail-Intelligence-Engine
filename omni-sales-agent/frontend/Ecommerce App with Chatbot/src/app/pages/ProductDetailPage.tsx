import { useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent } from '../components/ui/card';
import { fetchProducts, addToCart } from '../../services/api';
import { ShoppingCart, Star, Minus, Plus, ArrowLeft, Package, Truck } from 'lucide-react';
import { toast } from 'sonner';
import { Product } from '../types/product';

const formatINR = (value: number) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value || 0);

export function ProductDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [product, setProduct] = useState<Product | null>(null);
  const [quantity, setQuantity] = useState(1);

  useEffect(() => {
    fetchProducts().then((data) => {
      const products = data.products || data;
      const found = products.find((p: Product) => p._id === id || (p as any).id === id);
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

  const totalStock =
    product?.stock ??
    product?.available_stores?.reduce((sum, store) => sum + (store.stock || 0), 0) ??
    0;
  const productImage = product?.images?.[0] || '/fallback.png';

  const handleAddToCart = async () => {
    if (!product || totalStock === 0) {
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
      await addToCart(userId, product._id, quantity);
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
        <div className="space-y-4">
          <div className="relative">
            <img
              src={productImage}
              alt={product.name}
              className="w-full rounded-2xl shadow-lg object-cover aspect-square"
              onError={(e) => {
                e.currentTarget.src = '/fallback.png';
              }}
            />
            {totalStock === 0 && (
              <Badge className="absolute top-4 right-4" variant="destructive">
                Out of Stock
              </Badge>
            )}
          </div>

          {product.images?.length > 1 && (
            <div className="grid grid-cols-4 gap-3">
              {product.images.map((image, index) => (
                <img
                  key={`${image}-${index}`}
                  src={image}
                  alt={`${product.name} ${index + 1}`}
                  className="h-20 w-full rounded-xl object-cover border border-border/70"
                  onError={(e) => {
                    e.currentTarget.src = '/fallback.png';
                  }}
                />
              ))}
            </div>
          )}
        </div>

        <div>
          <div className="mb-4">
            <div className="flex flex-wrap gap-2 mb-3">
              <Badge>{product.category}</Badge>
              <Badge variant="secondary">{product.subcategory}</Badge>
            </div>
            <h1 className="text-4xl font-bold mb-2">{product.name}</h1>
            <div className="flex items-center space-x-2 mb-4">
              <div className="flex items-center">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    className={`h-5 w-5 ${
                      i < Math.floor(product.ratings || 0)
                        ? 'fill-yellow-400 text-yellow-400'
                        : 'text-gray-300'
                    }`}
                  />
                ))}
              </div>
              <span className="text-lg font-semibold">{product.ratings ?? 0}</span>
              <span className="text-muted-foreground">customer rating</span>
            </div>
            <p className="text-4xl font-bold text-primary mb-6">
              {formatINR(product.price)}
            </p>
          </div>

          <Card className="mb-6">
            <CardContent className="p-4">
              <h3 className="font-semibold mb-2">Description</h3>
              <p className="text-muted-foreground">{product.description}</p>
            </CardContent>
          </Card>

          <div className="flex items-center space-x-6 mb-6">
            <div className="flex items-center space-x-2">
              <Package className="h-5 w-5 text-muted-foreground" />
              <span className="text-sm">
                {totalStock > 0 ? (
                  <span className="text-green-600 font-semibold">
                    {totalStock} in stock
                  </span>
                ) : (
                  <span className="text-red-600 font-semibold">Out of stock</span>
                )}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <Truck className="h-5 w-5 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                Store pickup and shipping availability shown below
              </span>
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-4 mb-6">
            {product.attributes?.color && (
              <Card>
                <CardContent className="p-4">
                  <p className="text-sm text-muted-foreground">Color</p>
                  <p className="font-semibold">{product.attributes.color}</p>
                </CardContent>
              </Card>
            )}
            {product.attributes?.material && (
              <Card>
                <CardContent className="p-4">
                  <p className="text-sm text-muted-foreground">Material</p>
                  <p className="font-semibold">{product.attributes.material}</p>
                </CardContent>
              </Card>
            )}
          </div>

          {!!product.attributes?.size_available?.length && (
            <Card className="mb-6">
              <CardContent className="p-4">
                <h3 className="font-semibold mb-3">Available Sizes</h3>
                <div className="flex flex-wrap gap-2">
                  {product.attributes.size_available.map((size) => (
                    <Badge key={size} variant="outline">{size}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {!!product.tags?.length && (
            <Card className="mb-6">
              <CardContent className="p-4">
                <h3 className="font-semibold mb-3">Highlights</h3>
                <div className="flex flex-wrap gap-2">
                  {product.tags.map((tag) => (
                    <Badge key={tag} variant="secondary">{tag}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {!!product.available_stores?.length && (
            <Card className="mb-6">
              <CardContent className="p-4 space-y-3">
                <h3 className="font-semibold">Available Stores</h3>
                {product.available_stores.map((store) => (
                  <div
                    key={store.store_id}
                    className="flex items-center justify-between rounded-lg border border-border/70 px-3 py-2"
                  >
                    <span className="font-medium">{store.store_id}</span>
                    <span className="text-sm text-muted-foreground">{store.stock} in stock</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {totalStock > 0 && (
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
                    onClick={() => setQuantity(Math.min(totalStock, quantity + 1))}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
              </div>

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
