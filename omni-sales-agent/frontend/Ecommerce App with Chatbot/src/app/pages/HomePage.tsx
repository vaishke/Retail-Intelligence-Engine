import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ProductCard } from '../components/ProductCard';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Product } from '../types/product';
import { fetchProducts } from '../../services/api';
import { Sparkles, TrendingUp, Award, MessageSquare, Search } from 'lucide-react';
import { Chatbot } from '../components/Chatbot';

export function HomePage() {
  const [user, setUser] = useState<any>(null);
  const [chatbotOpen, setChatbotOpen] = useState(false);
  const [products, setProducts] = useState<Product[]>([]);
  const navigate = useNavigate();

  // ✅ Fetch user
  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem("token");

      if (!token) {
        navigate("/login");
        return;
      }

      try {
        const res = await fetch("http://localhost:8000/auth/me", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await res.json();

        if (data.success) {
          setUser(data.user);
        } else {
          navigate("/login");
        }
      } catch (err) {
        console.error(err);
        navigate("/login");
      }
    };

    fetchUser();
  }, [navigate]);

  // ✅ Fetch products from API
  useEffect(() => {
    fetchProducts().then((data) => {
      setProducts(data);
    });
  }, []);

  // ✅ Replace mock logic
  const featuredProducts = products.filter(p => p.featured);
  const recommendedProducts = products.slice(0, 4);

  return (
    <div className="container mx-auto px-4 py-6 md:py-8">
      
      {/* Chat Section */}
      <div className="mb-8 md:mb-12 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl md:rounded-2xl p-6 md:p-12">
        <div className="max-w-4xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-center mb-4 md:mb-6">
            <MessageSquare className="h-10 w-10 md:h-12 md:w-12 mb-3 md:mb-0 md:mr-4" />
            <div className="text-center">
              <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold mb-2">
                Hi {user?.name}! How can I help you today? 🤖
              </h1>
              <p className="text-base md:text-lg opacity-90">
                Ask me anything about products, orders, shipping, or rewards
              </p>
            </div>
          </div>

          <div 
            onClick={() => setChatbotOpen(true)}
            className="bg-white rounded-full p-2 shadow-2xl cursor-pointer hover:scale-[1.02]"
          >
            <div className="flex items-center px-4 py-3">
              <Search className="h-5 w-5 text-gray-400 mr-3" />
              <input
                placeholder="Type your question here..."
                className="flex-1 text-gray-700 outline-none bg-transparent"
                readOnly
              />
              <Button size="sm">
                <MessageSquare className="h-4 w-4 mr-2" />
                Chat
              </Button>
            </div>
          </div>

          <div className="flex gap-4 mt-6 justify-center">
            <Link to="/products">
              <Button variant="secondary">Shop Now</Button>
            </Link>
            <Link to="/rewards">
              <Button variant="outline" className="text-white border-white hover:bg-white/20">
                View Rewards
              </Button>
            </Link>
          </div>
        </div>
      </div>

      <Chatbot isOpen={chatbotOpen} onClose={() => setChatbotOpen(false)} />

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-12">
        <Card>
          <CardContent className="p-6 flex items-center space-x-4">
            <Award className="text-blue-600" />
            <div>
              <p className="text-sm text-muted-foreground">Loyalty Points</p>
              <p className="text-2xl font-bold">{user?.loyalty?.points || 0}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 flex items-center space-x-4">
            <TrendingUp className="text-green-600" />
            <div>
              <p className="text-sm text-muted-foreground">Active Orders</p>
              {/* 🔥 Replace storage */}
              <p className="text-2xl font-bold">
                {JSON.parse(localStorage.getItem('orders') || '[]').length}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 flex items-center space-x-4">
            <Sparkles className="text-purple-600" />
            <div>
              <p className="text-sm text-muted-foreground">Available Coupons</p>
              <p className="text-2xl font-bold">3</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recommended */}
      <section className="mb-12">
        <h2 className="text-3xl font-bold mb-4">Recommended for You</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          {recommendedProducts.map(product => (
            <ProductCard key={product._id} product={product} />
          ))}
        </div>
      </section>

      {/* Featured */}
      {/* <section>
        <h2 className="text-3xl font-bold mb-4">Featured Products</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          {featuredProducts.map(product => (
            <ProductCard key={product._id} product={product} />
          ))}
        </div>
      </section> */}

    </div>
  );
}