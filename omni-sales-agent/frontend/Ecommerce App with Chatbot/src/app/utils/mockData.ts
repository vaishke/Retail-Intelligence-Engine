// Mock data and utilities for the e-commerce application

export interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  image: string;
  category: string;
  stock: number;
  rating: number;
  featured: boolean;
}

export interface User {
  id: string;
  name: string;
  email: string;
  loyaltyPoints: number;
  memberSince: string;
}

export interface CartItem {
  productId: string;
  quantity: number;
}

export interface Order {
  id: string;
  userId: string;
  items: { productId: string; quantity: number; price: number }[];
  total: number;
  status: 'confirmed' | 'shipped' | 'delivered';
  createdAt: string;
  shipmentId?: string;
  invoiceId?: string;
  trackingUrl?: string;
}

export interface Coupon {
  id: string;
  code: string;
  discount: number;
  expiresAt: string;
  minPurchase: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent';
  content: string | { message: string; products?: any[]; prompt?: string };
  timestamp: string;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: string;
}

// Mock products
export const mockProducts: Product[] = [
  {
    id: '1',
    name: 'Premium Wireless Headphones',
    description: 'High-quality noise-canceling headphones with 40-hour battery life',
    price: 299.99,
    image: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500',
    category: 'Electronics',
    stock: 15,
    rating: 4.8,
    featured: true,
  },
  {
    id: '2',
    name: 'Smart Fitness Watch',
    description: 'Track your health and fitness with advanced sensors',
    price: 249.99,
    image: 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500',
    category: 'Wearables',
    stock: 8,
    rating: 4.6,
    featured: true,
  },
  {
    id: '3',
    name: 'Mechanical Gaming Keyboard',
    description: 'RGB backlit mechanical keyboard with Cherry MX switches',
    price: 159.99,
    image: 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500',
    category: 'Accessories',
    stock: 20,
    rating: 4.9,
    featured: false,
  },
  {
    id: '4',
    name: 'Portable Bluetooth Speaker',
    description: 'Waterproof speaker with 360° sound and 24-hour battery',
    price: 89.99,
    image: 'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=500',
    category: 'Audio',
    stock: 0,
    rating: 4.5,
    featured: false,
  },
  {
    id: '5',
    name: 'Laptop Stand Aluminum',
    description: 'Ergonomic adjustable laptop stand for better posture',
    price: 49.99,
    image: 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=500',
    category: 'Accessories',
    stock: 30,
    rating: 4.7,
    featured: true,
  },
  {
    id: '6',
    name: '4K Webcam Pro',
    description: 'Professional 4K webcam with auto-focus and HDR',
    price: 179.99,
    image: 'https://images.unsplash.com/photo-1585060544812-6b45742d762f?w=500',
    category: 'Electronics',
    stock: 12,
    rating: 4.8,
    featured: false,
  },
  {
    id: '7',
    name: 'Wireless Mouse Ergonomic',
    description: 'Comfortable ergonomic mouse with precision tracking',
    price: 39.99,
    image: 'https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500',
    category: 'Accessories',
    stock: 25,
    rating: 4.4,
    featured: false,
  },
  {
    id: '8',
    name: 'USB-C Hub Multi-Port',
    description: '7-in-1 USB-C hub with HDMI, USB 3.0, and SD card reader',
    price: 59.99,
    image: 'https://images.unsplash.com/photo-1625948515291-69613efd103f?w=500',
    category: 'Accessories',
    stock: 18,
    rating: 4.6,
    featured: true,
  },
];

// Mock coupons
export const mockCoupons: Coupon[] = [
  {
    id: '1',
    code: 'WELCOME10',
    discount: 10,
    expiresAt: '2025-12-31',
    minPurchase: 50,
  },
  {
    id: '2',
    code: 'LOYALTY20',
    discount: 20,
    expiresAt: '2025-06-30',
    minPurchase: 100,
  },
  {
    id: '3',
    code: 'FLASH15',
    discount: 15,
    expiresAt: '2025-01-31',
    minPurchase: 75,
  },
];

// LocalStorage helpers
export const storage = {
  getUser: (): User | null => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },
  setUser: (user: User) => {
    localStorage.setItem('user', JSON.stringify(user));
  },
  clearUser: () => {
    localStorage.removeItem('user');
  },
  getCart: (): CartItem[] => {
    const cart = localStorage.getItem('cart');
    return cart ? JSON.parse(cart) : [];
  },
  setCart: (cart: CartItem[]) => {
    localStorage.setItem('cart', JSON.stringify(cart));
  },
  getOrders: (): Order[] => {
    const orders = localStorage.getItem('orders');
    return orders ? JSON.parse(orders) : [];
  },
  setOrders: (orders: Order[]) => {
    localStorage.setItem('orders', JSON.stringify(orders));
  },
  getChatSessions: (): ChatSession[] => {
    const sessions = localStorage.getItem('chatSessions');
    return sessions ? JSON.parse(sessions) : [];
  },
  setChatSessions: (sessions: ChatSession[]) => {
    localStorage.setItem('chatSessions', JSON.stringify(sessions));
  },
};

// Mock AI agent responses
export const getAgentResponse = (message: string): string => {
  const lowerMessage = message.toLowerCase();
  
  if (lowerMessage.includes('order') || lowerMessage.includes('track')) {
    return 'I can help you track your order! Please provide your order ID, and I\'ll give you the latest shipping status.';
  }
  
  if (lowerMessage.includes('return') || lowerMessage.includes('refund')) {
    return 'We offer a 30-day return policy for most items. Refunds are processed within 5-7 business days after we receive the item. Would you like to initiate a return?';
  }
  
  if (lowerMessage.includes('product') || lowerMessage.includes('recommend')) {
    return 'Based on your browsing history, I recommend checking out our Premium Wireless Headphones and Smart Fitness Watch. They\'re currently our bestsellers!';
  }
  
  if (lowerMessage.includes('coupon') || lowerMessage.includes('discount')) {
    return 'Great news! Use code WELCOME10 for 10% off your first order over $50, or LOYALTY20 for 20% off orders over $100. Check your profile for personalized offers!';
  }
  
  if (lowerMessage.includes('ship') || lowerMessage.includes('delivery')) {
    return 'We offer free standard shipping (5-7 business days) on orders over $75. Express shipping is available for $15 and takes 2-3 business days.';
  }
  
  if (lowerMessage.includes('loyalty') || lowerMessage.includes('points')) {
    return 'You earn 1 loyalty point for every dollar spent! Points can be redeemed for discounts: 100 points = $10 off. You currently have points in your account.';
  }
  
  return 'Thank you for your message! I\'m here to help with orders, products, shipping, returns, and more. How can I assist you today?';
};
