import { Link } from 'react-router-dom';
import { ShoppingCart, Star } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardFooter } from './ui/card';
import { Badge } from './ui/badge';
import { Product } from '../types/product';
import { toast } from 'sonner';
import { addToCart as addToCartApi } from '../../services/api';

interface ProductCardProps {
  product: Product;
}

export function ProductCard({ product }: ProductCardProps) {
  const stock =
    product.stock ??
    product.available_stores?.reduce((sum, store) => sum + (store.stock || 0), 0) ??
    0;

  const addToCart = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (stock === 0) {
      toast.error('Product is out of stock');
      return;
    }

    const user = JSON.parse(localStorage.getItem("user") || "{}");
    const userId = user.user_id || user.id;

    if (!userId) {
      toast.error('Please log in to add items to cart');
      return;
    }

    try {
      await addToCartApi(userId, product._id, 1);
      window.dispatchEvent(new Event("storage"));
      toast.success('Added to cart');
    } catch (error) {
      console.error(error);
      toast.error('Failed to add to cart');
    }
  };

  const image = product.images?.[0] || '/fallback.png';

  return (
    <Link to={`/product/${product._id}`} target="_blank" rel="noreferrer">
      <Card className="h-full hover:shadow-lg transition-all duration-300 group overflow-hidden">
        
        {/* IMAGE */}
        <div className="relative overflow-hidden">
          <img
            src={image}
            alt={product.name}
            className="w-full h-40 md:h-48 object-cover group-hover:scale-110 transition-transform duration-300"
            onError={(e) => {
              e.currentTarget.src = '/fallback.png';
            }}
          />

          {stock === 0 && (
            <Badge className="absolute top-2 right-2 text-xs" variant="destructive">
              Out of Stock
            </Badge>
          )}

          {product.featured && stock > 0 && (
            <Badge className="absolute top-2 right-2 text-xs" variant="default">
              Featured
            </Badge>
          )}
        </div>

        {/* CONTENT */}
        <CardContent className="p-3 md:p-4">
          <h3 className="font-semibold text-sm md:text-base mb-2 line-clamp-1">
            {product.name}
          </h3>

          <p className="text-xs md:text-sm text-muted-foreground mb-3 line-clamp-2">
            {product.description}
          </p>

          <div className="flex items-center space-x-1 mb-2">
            <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
            <span className="text-sm">{product.ratings ?? 0}</span>
            <span className="text-sm text-muted-foreground">
              ({stock} in stock)
            </span>
          </div>
        </CardContent>

        {/* FOOTER */}
        <CardFooter className="p-3 md:p-4 pt-0 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
          <span className="text-xl md:text-2xl font-bold">
            ₹{product.price}
          </span>

          <Button
            size="sm"
            onClick={addToCart}
            disabled={stock === 0}
            className="w-full sm:w-auto text-xs md:text-sm"
          >
            <ShoppingCart className="h-4 w-4 mr-2" />
            Add to Cart
          </Button>
        </CardFooter>

      </Card>
    </Link>
  );
}
