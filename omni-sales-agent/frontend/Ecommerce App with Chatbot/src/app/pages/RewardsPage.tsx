import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { mockCoupons, storage } from '../utils/mockData';
import { Gift, Tag, Award, Copy } from 'lucide-react';
import { toast } from 'sonner';

export function RewardsPage() {
  const user = storage.getUser();

  if (!user) return null;

  const copyCoupon = (code: string) => {
    navigator.clipboard.writeText(code);
    toast.success('Coupon code copied!');
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8">Rewards & Coupons</h1>

      {/* Loyalty Overview */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Award className="h-6 w-6 mr-2 text-primary" />
            Your Loyalty Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center p-6 bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-lg">
              <p className="text-sm mb-2 opacity-90">Total Points</p>
              <p className="text-5xl font-bold mb-2">{user.loyaltyPoints}</p>
              <p className="text-sm opacity-90">Available to redeem</p>
            </div>
            <div className="text-center p-6 border rounded-lg">
              <p className="text-sm text-muted-foreground mb-2">Redeemable Value</p>
              <p className="text-4xl font-bold mb-2">
                ${Math.floor(user.loyaltyPoints / 100) * 10}
              </p>
              <p className="text-sm text-muted-foreground">100 points = $10 off</p>
            </div>
            <div className="text-center p-6 border rounded-lg">
              <p className="text-sm text-muted-foreground mb-2">Points to Next Tier</p>
              <p className="text-4xl font-bold mb-2">
                {500 - (user.loyaltyPoints % 500)}
              </p>
              <p className="text-sm text-muted-foreground">Reach 500 for bonus reward</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Available Coupons */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">Available Coupons</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {mockCoupons.map(coupon => (
            <Card key={coupon.id} className="border-2 border-dashed">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center">
                    <Tag className="h-5 w-5 mr-2 text-primary" />
                    <CardTitle>{coupon.discount}% OFF</CardTitle>
                  </div>
                  <Badge variant="secondary">Active</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="bg-muted p-3 rounded-lg font-mono text-center text-xl font-bold">
                    {coupon.code}
                  </div>
                  <div className="space-y-2 text-sm text-muted-foreground">
                    <p>• Min. purchase: ${coupon.minPurchase}</p>
                    <p>• Expires: {new Date(coupon.expiresAt).toLocaleDateString()}</p>
                  </div>
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => copyCoupon(coupon.code)}
                  >
                    <Copy className="h-4 w-4 mr-2" />
                    Copy Code
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* How It Works */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Gift className="h-6 w-6 mr-2" />
            How Loyalty Rewards Work
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl font-bold text-blue-600">1</span>
              </div>
              <h3 className="font-semibold mb-2">Shop</h3>
              <p className="text-sm text-muted-foreground">
                Make purchases on our platform
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl font-bold text-purple-600">2</span>
              </div>
              <h3 className="font-semibold mb-2">Earn Points</h3>
              <p className="text-sm text-muted-foreground">
                Get 1 point per dollar spent
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl font-bold text-green-600">3</span>
              </div>
              <h3 className="font-semibold mb-2">Redeem</h3>
              <p className="text-sm text-muted-foreground">
                100 points = $10 discount
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl font-bold text-orange-600">4</span>
              </div>
              <h3 className="font-semibold mb-2">Save More</h3>
              <p className="text-sm text-muted-foreground">
                Enjoy exclusive member benefits
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
