import { View, Text } from 'react-native';
import Animated, { FadeInLeft, FadeInRight } from 'react-native-reanimated';

export interface Message { id: string; role: 'user' | 'assistant'; content: string; }

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  return (
    <Animated.View entering={isUser ? FadeInRight.springify() : FadeInLeft.springify()} style={{ alignItems: isUser ? 'flex-end' : 'flex-start', marginVertical: 2 }}>
      <View style={{ maxWidth: '85%', backgroundColor: isUser ? '#6C63FF' : '#1A1A2E', borderRadius: 18, borderBottomRightRadius: isUser ? 4 : 18, borderBottomLeftRadius: isUser ? 18 : 4, paddingHorizontal: 16, paddingVertical: 12, borderWidth: isUser ? 0 : 1, borderColor: '#2A2A3E' }}>
        <Text style={{ color: '#E0E0E8', fontSize: 15, lineHeight: 22 }}>{message.content}</Text>
      </View>
    </Animated.View>
  );
}