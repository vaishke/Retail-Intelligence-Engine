import { Link, useNavigate } from 'react-router-dom';
import { ShoppingCart, User, Store, MessageCircle as MessageCircleIcon, Menu, X, Package, Award } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { useState, useEffect } from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger, SheetDescription } from './ui/sheet';
import { fetchCart } from '../../services/api';

interface HeaderProps {
  onChatClick: () => void;
}

export function Header({ onChatClick }: HeaderProps) {
  const [cartCount, setCartCount] = useState(0);
  const [user, setUser] = useState<any>(null);
  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem("token");

      if (!token) {
        setUser(null);
        return;
      }

      try {
        const res = await fetch("http://localhost:8000/auth/me", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!res.ok) {
          setUser(null);
          return;
        }

        const data = await res.json();

        if (data.user) {
          setUser(data.user);
          localStorage.setItem("user", JSON.stringify(data.user));
        } else {
          setUser(null);
        }
      } catch (err) {
        console.error(err);
        setUser(null);
      }
    };

    fetchUser();

    const handleStorageChange = () => {
      const storedUser = localStorage.getItem("user");
      setUser(storedUser ? JSON.parse(storedUser) : null);
    };

    window.addEventListener("storage", handleStorageChange);

    return () => {
      window.removeEventListener("storage", handleStorageChange);
    };
  }, []);
  // window.location.reload();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const updateCart = async () => {
      const storedUser = JSON.parse(localStorage.getItem("user") || "{}");
      const userId = storedUser.user_id || storedUser.id;

      if (!userId) {
        setCartCount(0);
        return;
      }

      try {
        const cartRes = await fetchCart(userId);
        const items = cartRes.cart || [];
        setCartCount(items.reduce((sum: number, item: any) => sum + (item.quantity || item.qty || 0), 0));
      } catch {
        setCartCount(0);
      }
    };

    updateCart();
    const handleStorageChange = () => {
      updateCart();
    };
    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.dispatchEvent(new Event("storage"));
    setUser(null);
    navigate("/login");
    window.location.reload(); // force UI sync
  };

  return (
    <header className="sticky top-0 z-50 bg-white border-b shadow-sm">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center space-x-2">
          <Store className="h-6 w-6 md:h-8 md:w-8 text-primary" />
          <span className="font-bold text-lg md:text-xl">TechMart</span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center space-x-6">
          <Link to="/" className="text-sm hover:text-primary transition-colors">
            Home
          </Link>
          <Link to="/products" className="text-sm hover:text-primary transition-colors">
            Products
          </Link>
          <Link to="/orders" className="text-sm hover:text-primary transition-colors">
            Orders
          </Link>
        </nav>

        {/* Desktop Actions */}
        <div className="hidden md:flex items-center space-x-4">
          {/* Chatbot Button */}
          <Button
            variant="outline"
            size="icon"
            onClick={onChatClick}
            className="relative"
          >
            <MessageCircleIcon className="h-5 w-5" />
          </Button>

          {/* Cart Button */}
          <Link to="/cart">
            <Button variant="outline" size="icon" className="relative">
              <ShoppingCart className="h-5 w-5" />
              {cartCount > 0 && (
                <Badge className="absolute -top-2 -right-2 h-5 w-5 flex items-center justify-center p-0 text-xs">
                  {cartCount}
                </Badge>
              )}
            </Button>
          </Link>

          {/* Profile Button */}
          {user ? (
            <div className="flex items-center space-x-2">
              <Link to="/profile">
                <Button variant="outline" size="icon">
                  <User className="h-5 w-5" />
                </Button>
              </Link>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                Logout
              </Button>
            </div>
          ) : (
            <Link to="/login">
              <Button>Login</Button>
            </Link>
          )}
        </div>

        {/* Mobile Actions */}
        <div className="flex md:hidden items-center space-x-2">
          {/* Chatbot Button */}
          <Button
            variant="ghost"
            size="icon"
            onClick={onChatClick}
            className="relative h-9 w-9"
          >
            <MessageCircleIcon className="h-5 w-5" />
          </Button>

          {/* Cart Button */}
          <Link to="/cart">
            <Button variant="ghost" size="icon" className="relative h-9 w-9">
              <ShoppingCart className="h-5 w-5" />
              {cartCount > 0 && (
                <Badge className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs">
                  {cartCount}
                </Badge>
              )}
            </Button>
          </Link>

          {/* Mobile Menu */}
          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="h-9 w-9">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[280px]">
              <SheetHeader>
                <SheetTitle>Menu</SheetTitle>
                <SheetDescription>
                  Navigate through TechMart
                </SheetDescription>
              </SheetHeader>
              <div className="flex flex-col space-y-4 mt-6">
                {user && (
                  <div className="pb-4 border-b">
                    <p className="font-semibold">{user.name}</p>
                    <p className="text-sm text-muted-foreground">{user.email}</p>
                  </div>
                )}
                
                <Link 
                  to="/" 
                  className="flex items-center space-x-3 p-3 rounded-lg hover:bg-muted transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Store className="h-5 w-5" />
                  <span>Home</span>
                </Link>
                
                <Link 
                  to="/products" 
                  className="flex items-center space-x-3 p-3 rounded-lg hover:bg-muted transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Package className="h-5 w-5" />
                  <span>Products</span>
                </Link>
                
                <Link 
                  to="/orders" 
                  className="flex items-center space-x-3 p-3 rounded-lg hover:bg-muted transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Package className="h-5 w-5" />
                  <span>Orders</span>
                </Link>
                
                <Link 
                  to="/rewards" 
                  className="flex items-center space-x-3 p-3 rounded-lg hover:bg-muted transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Award className="h-5 w-5" />
                  <span>Rewards</span>
                </Link>
                
                {user && (
                  <Link 
                    to="/profile" 
                    className="flex items-center space-x-3 p-3 rounded-lg hover:bg-muted transition-colors"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <User className="h-5 w-5" />
                    <span>Profile</span>
                  </Link>
                )}
                
                <div className="pt-4 border-t">
                  {user ? (
                    <Button 
                      variant="outline" 
                      className="w-full" 
                      onClick={() => {
                        handleLogout();
                        setMobileMenuOpen(false);
                      }}
                    >
                      Logout
                    </Button>
                  ) : (
                    <Button 
                      className="w-full" 
                      onClick={() => {
                        navigate('/login');
                        setMobileMenuOpen(false);
                      }}
                    >
                      Login
                    </Button>
                  )}
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
