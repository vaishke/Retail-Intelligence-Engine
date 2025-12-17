import { View, Text, Pressable, StyleSheet } from "react-native";
import { Link } from "expo-router";

export default function Home() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>🛍 Omni Sales Agent</Text>
      <Text style={styles.subtitle}>
        AI-powered unified shopping experience
      </Text>

      <Link href="/chat" asChild>
        <Pressable style={styles.button}>
          <Text style={styles.buttonText}>Start Chat</Text>
        </Pressable>
      </Link>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", alignItems: "center" },
  title: { fontSize: 26, fontWeight: "bold" },
  subtitle: { marginVertical: 10, color: "#666" },
  button: { backgroundColor: "#000", padding: 12, borderRadius: 8 },
  buttonText: { color: "#fff" }
});
