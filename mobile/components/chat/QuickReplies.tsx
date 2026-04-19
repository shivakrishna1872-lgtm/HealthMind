import { ScrollView, TouchableOpacity, Text } from 'react-native';
import Animated, { FadeInUp } from 'react-native-reanimated';
import * as Haptics from 'expo-haptics';

export function QuickReplies({ replies, onSelect }: { replies: string[]; onSelect: (t: string) => void }) {
  if (!replies?.length) return null;
  return (
    <Animated.View entering={FadeInUp.springify()} style={{ paddingVertical: 8 }}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 16, gap: 8 }}>
        {replies.map((r, i) => (
          <TouchableOpacity key={i} onPress={async () => { await Haptics.selectionAsync(); onSelect(r); }}
            style={{ backgroundColor: '#1A1A2E', borderRadius: 20, paddingHorizontal: 16, paddingVertical: 10, borderWidth: 1, borderColor: '#6C63FF55' }}>
            <Text style={{ color: '#A0A0CC', fontSize: 14 }}>{r}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </Animated.View>
  );
}