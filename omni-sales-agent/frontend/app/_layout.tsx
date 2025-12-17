// app/_layout.tsx
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import LoginScreen from './login';
import RegisterScreen from './register';
import HomeScreen from './index';
import ProductsScreen from './products';
import ProductDetailsScreen from './product-details';
import CartScreen from './cart';
import CheckoutScreen from './checkout';
import CouponsScreen from './coupons';

const Stack = createNativeStackNavigator();

export default function Layout() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Login">
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="Register" component={RegisterScreen} />
        <Stack.Screen name="Home" component={HomeScreen} />
        <Stack.Screen name="Products" component={ProductsScreen} />
        <Stack.Screen name="ProductDetails" component={ProductDetailsScreen} />
        <Stack.Screen name="Cart" component={CartScreen} />
        <Stack.Screen name="Checkout" component={CheckoutScreen} />
        <Stack.Screen name="Coupons" component={CouponsScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
