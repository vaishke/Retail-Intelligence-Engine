import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Award, Mail, Calendar, Gift, TrendingUp } from 'lucide-react';
import { Progress } from '../components/ui/progress';
import { useEffect, useState } from 'react';

export function ProfilePage() {
  const navigate = useNavigate();  

  const [user, setUser] = useState<any>(null);

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

        if (!res.ok) {
          navigate("/login");
          return;
        }

        const data = await res.json();

        if (data.user) {
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

  if (!user) return null;

  // ✅ SAFE FALLBACKS (no backend? no crash 😌)
  const loyaltyPoints = user.loyaltyPoints ?? 0;
  const memberSince = user.memberSince ?? new Date();

  // ✅ FIXED LOGIC (handles 0 correctly)
  const remainder = loyaltyPoints % 500;
  const pointsToNextReward = remainder === 0 ? 500 : 500 - remainder;
  const progress = (remainder / 500) * 100;

  return (
    <div className="container mx-auto px-4 py-6 md:py-8">
      <h1 className="text-3xl md:text-4xl font-bold mb-6 md:mb-8">My Profile</h1>

      <div className="grid lg:grid-cols-3 gap-4 md:gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg md:text-xl">Account Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 md:space-y-6">
            <div className="flex items-center space-x-3 md:space-x-4">
              <div className="h-16 w-16 md:h-20 md:w-20 rounded-full bg-primary flex items-center justify-center text-white text-2xl md:text-3xl font-bold flex-shrink-0">
                {user.name?.charAt(0)?.toUpperCase() || "U"}
              </div>
              <div>
                <h2 className="text-xl md:text-2xl font-bold">{user.name}</h2>
                <Badge className="mt-1 text-xs">Premium Member</Badge>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
              <div className="flex items-center space-x-3">
                <Mail className="h-4 w-4 md:h-5 md:w-5 text-muted-foreground flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-xs md:text-sm text-muted-foreground">Email</p>
                  <p className="font-semibold text-sm md:text-base truncate">{user.email}</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Calendar className="h-4 w-4 md:h-5 md:w-5 text-muted-foreground flex-shrink-0" />
                <div>
                  <p className="text-xs md:text-sm text-muted-foreground">Member Since</p>
                  <p className="font-semibold text-sm md:text-base">
                    {new Date(memberSince).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* ✅ LOYALTY SECTION FIXED */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-lg md:text-xl">
              <Award className="h-4 w-4 md:h-5 md:w-5 mr-2" />
              Loyalty Points
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center mb-4 md:mb-6">
              <p className="text-4xl md:text-5xl font-bold text-primary mb-2">
                {loyaltyPoints}
              </p>
              <p className="text-xs md:text-sm text-muted-foreground">
                Points Available
              </p>
            </div>

            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs md:text-sm mb-2">
                  <span>Next Reward</span>
                  <span className="font-semibold">
                    {pointsToNextReward} pts away
                  </span>
                </div>

                <Progress value={progress} />
              </div>

              <Button
                className="w-full text-sm md:text-base"
                variant="outline"
                disabled={loyaltyPoints < 100}
              >
                {loyaltyPoints >= 100
                  ? "Redeem Rewards"
                  : "Earn more to unlock rewards"}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle className="text-lg md:text-xl">Loyalty Benefits</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
              <div className="flex items-start space-x-3">
                <div className="p-2 md:p-3 bg-blue-100 rounded-lg flex-shrink-0">
                  <TrendingUp className="h-5 w-5 md:h-6 md:w-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm md:text-base mb-1">Earn Points</h3>
                  <p className="text-xs md:text-sm text-muted-foreground">
                    Get 1 point for every dollar spent
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="p-2 md:p-3 bg-purple-100 rounded-lg flex-shrink-0">
                  <Gift className="h-5 w-5 md:h-6 md:w-6 text-purple-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm md:text-base mb-1">Redeem Rewards</h3>
                  <p className="text-xs md:text-sm text-muted-foreground">
                    100 points = $10 off your order
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="p-2 md:p-3 bg-green-100 rounded-lg flex-shrink-0">
                  <Award className="h-5 w-5 md:h-6 md:w-6 text-green-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm md:text-base mb-1">Exclusive Deals</h3>
                  <p className="text-xs md:text-sm text-muted-foreground">
                    Early access to sales and special offers
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}