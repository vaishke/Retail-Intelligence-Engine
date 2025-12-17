// app/_layout.tsx
import { Stack } from 'expo-router';

export default function Layout() {
  return (
    <Stack>
      <Stack.Screen name="login" options={{ headerShown: false }} />
      <Stack.Screen name="register" options={{ headerShown: false }} />
      <Stack.Screen name="index" options={{ title: 'Home' }} />
      <Stack.Screen name="products" options={{ title: 'Products' }} />
      <Stack.Screen name="product-details" options={{ title: 'Product Details' }} />
      <Stack.Screen name="cart" options={{ title: 'Cart' }} />
      <Stack.Screen name="checkout" options={{ title: 'Checkout' }} />
      <Stack.Screen name="coupons" options={{ title: 'Coupons' }} />
    </Stack>
  );
}
