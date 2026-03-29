import { Link } from 'react-router-dom';
import { ShoppingCart, Star } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardFooter } from './ui/card';
import { Badge } from './ui/badge';
import { Product, storage } from '../utils/mockData';
import { toast } from 'sonner';

interface ProductCardProps {
  product: Product;
}

export function ProductCard({ product }: ProductCardProps) {
  const addToCart = (e: React.MouseEvent) => {
    e.preventDefault();
    
    if (product.stock === 0) {
      toast.error('Product is out of stock');
      return;
    }

    const cart = storage.getCart();
    const existingItem = cart.find(item => item.productId === product.id);

    if (existingItem) {
      if (existingItem.quantity < product.stock) {
        existingItem.quantity += 1;
        storage.setCart(cart);
        toast.success('Added to cart');
      } else {
        toast.error('Cannot add more than available stock');
      }
    } else {
      storage.setCart([...cart, { productId: product.id, quantity: 1 }]);
      toast.success('Added to cart');
    }
  };

  return (
    <Link to={`/product/${product.id}`}>
      <Card className="h-full hover:shadow-lg transition-all duration-300 group overflow-hidden">
        <div className="relative overflow-hidden">
          <img
            src={product.image}
            alt={product.name}
            className="w-full h-40 md:h-48 object-cover group-hover:scale-110 transition-transform duration-300"
          />
          {product.stock === 0 && (
            <Badge className="absolute top-1.5 right-1.5 md:top-2 md:right-2 text-xs" variant="destructive">
              Out of Stock
            </Badge>
          )}
          {product.featured && product.stock > 0 && (
            <Badge className="absolute top-1.5 right-1.5 md:top-2 md:right-2 text-xs" variant="default">
              Featured
            </Badge>
          )}
        </div>
        <CardContent className="p-3 md:p-4">
          <h3 className="font-semibold text-sm md:text-base mb-1 md:mb-2 line-clamp-1">{product.name}</h3>
          <p className="text-xs md:text-sm text-muted-foreground mb-2 md:mb-3 line-clamp-2">
            {product.description}
          </p>
          <div className="flex items-center space-x-1 mb-2">
            <Star className="h-3 w-3 md:h-4 md:w-4 fill-yellow-400 text-yellow-400" />
            <span className="text-xs md:text-sm">{product.rating}</span>
            <span className="text-xs md:text-sm text-muted-foreground">
              ({product.stock} in stock)
            </span>
          </div>
        </CardContent>
        <CardFooter className="p-3 md:p-4 pt-0 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
          <span className="text-xl md:text-2xl font-bold">${product.price}</span>
          <Button
            size="sm"
            onClick={addToCart}
            disabled={product.stock === 0}
            className="w-full sm:w-auto text-xs md:text-sm"
          >
            <ShoppingCart className="h-3 w-3 md:h-4 md:w-4 md:mr-2" />
            <span className="hidden sm:inline">Add to Cart</span>
            <span className="sm:hidden">Add</span>
          </Button>
        </CardFooter>
      </Card>
    </Link>
  );
}