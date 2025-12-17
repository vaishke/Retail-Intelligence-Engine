import { View, TextInput, FlatList, Text, Pressable } from "react-native";
import { useState } from "react";

export default function Chat() {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    const userMsg = { role: "user", text: input };
    setMessages([...messages, userMsg]);

    // API call will come here
    setInput("");
  };

  return (
    <View style={{ flex: 1, padding: 16 }}>
      <FlatList
        data={messages}
        renderItem={({ item }) => (
          <Text>{item.role}: {item.text}</Text>
        )}
      />

      <TextInput
        value={input}
        onChangeText={setInput}
        placeholder="Ask me anything..."
      />

      <Pressable onPress={sendMessage}>
        <Text>Send</Text>
      </Pressable>
    </View>
  );
}
