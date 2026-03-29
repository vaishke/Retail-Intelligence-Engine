import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ProductCard } from '../components/ProductCard';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { mockProducts, storage } from '../utils/mockData';
import { Sparkles, TrendingUp, Award, MessageSquare, Search } from 'lucide-react';
import { Chatbot } from '../components/Chatbot';

export function HomePage() {
  const [user, setUser] = useState(storage.getUser());
  const [chatbotOpen, setChatbotOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      navigate('/login');
    }
  }, [user, navigate]);

  const featuredProducts = mockProducts.filter(p => p.featured);
  const recommendedProducts = mockProducts.slice(0, 4);

  return (
    <div className="container mx-auto px-4 py-6 md:py-8">
      {/* AI Chatbot Search Bar */}
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
          
          {/* Search Bar */}
          <div 
            onClick={() => setChatbotOpen(true)}
            className="bg-white rounded-full p-1.5 md:p-2 shadow-2xl cursor-pointer hover:shadow-3xl transition-all duration-300 hover:scale-[1.02]"
          >
            <div className="flex items-center px-3 md:px-4 py-2 md:py-3">
              <Search className="h-5 w-5 md:h-6 md:w-6 text-gray-400 mr-2 md:mr-3 flex-shrink-0" />
              <input
                type="text"
                placeholder="Type your question here..."
                className="flex-1 text-gray-700 text-sm md:text-lg outline-none bg-transparent cursor-pointer"
                onFocus={() => setChatbotOpen(true)}
                readOnly
              />
              <Button 
                size="sm"
                className="rounded-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 md:px-6"
              >
                <MessageSquare className="h-4 w-4 md:mr-2" />
                <span className="hidden md:inline">Chat Now</span>
              </Button>
            </div>
          </div>

          {/* Quick Action Buttons */}
          <div className="flex flex-wrap gap-3 md:gap-4 mt-4 md:mt-6 justify-center">
            <Link to="/products">
              <Button size="sm" className="md:text-base" variant="secondary">
                Shop Now
              </Button>
            </Link>
            <Link to="/rewards">
              <Button size="sm" variant="outline" className="text-white border-white hover:bg-white/20 md:text-base">
                View Rewards
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Chatbot Component */}
      <Chatbot isOpen={chatbotOpen} onClose={() => setChatbotOpen(false)} />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 md:gap-6 mb-8 md:mb-12">
        <Card>
          <CardContent className="p-4 md:p-6 flex items-center space-x-3 md:space-x-4">
            <div className="p-2 md:p-3 bg-blue-100 rounded-lg">
              <Award className="h-5 w-5 md:h-6 md:w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-xs md:text-sm text-muted-foreground">Loyalty Points</p>
              <p className="text-xl md:text-2xl font-bold">{user?.loyaltyPoints || 0}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 md:p-6 flex items-center space-x-3 md:space-x-4">
            <div className="p-2 md:p-3 bg-green-100 rounded-lg">
              <TrendingUp className="h-5 w-5 md:h-6 md:w-6 text-green-600" />
            </div>
            <div>
              <p className="text-xs md:text-sm text-muted-foreground">Active Orders</p>
              <p className="text-xl md:text-2xl font-bold">{storage.getOrders().length}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 md:p-6 flex items-center space-x-3 md:space-x-4">
            <div className="p-2 md:p-3 bg-purple-100 rounded-lg">
              <Sparkles className="h-5 w-5 md:h-6 md:w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-xs md:text-sm text-muted-foreground">Available Coupons</p>
              <p className="text-xl md:text-2xl font-bold">3</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recommended Products */}
      <section className="mb-8 md:mb-12">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 md:mb-6 gap-3">
          <div>
            <h2 className="text-2xl md:text-3xl font-bold mb-1 md:mb-2">Recommended for You</h2>
            <p className="text-sm md:text-base text-muted-foreground">
              Handpicked products based on your preferences
            </p>
          </div>
          <Link to="/products">
            <Button variant="outline" size="sm" className="md:text-base">View All</Button>
          </Link>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-6">
          {recommendedProducts.map(product => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      </section>

      {/* Featured Products */}
      <section>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 md:mb-6 gap-3">
          <div>
            <h2 className="text-2xl md:text-3xl font-bold mb-1 md:mb-2">Featured Products</h2>
            <p className="text-sm md:text-base text-muted-foreground">
              Our top picks for this month
            </p>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-6">
          {featuredProducts.map(product => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      </section>
    </div>
  );
}