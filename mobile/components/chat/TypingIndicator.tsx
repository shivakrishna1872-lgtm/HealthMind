import { View } from 'react-native';
import Animated, { FadeIn, useSharedValue, useAnimatedStyle, withRepeat, withTiming, withDelay } from 'react-native-reanimated';
import { useEffect } from 'react';

function Dot({ delay }: { delay: number }) {
  const opacity = useSharedValue(0.3);
  useEffect(() => { opacity.value = withDelay(delay, withRepeat(withTiming(1, { duration: 400 }), -1, true)); }, []);
  const style = useAnimatedStyle(() => ({ opacity: opacity.value }));
  return <Animated.View style={[{ width: 8, height: 8, borderRadius: 4, backgroundColor: '#8E8E93' }, style]} />;
}

export function TypingIndicator() {
  return (
    <Animated.View entering={FadeIn.duration(200)} style={{ alignItems: 'flex-start', marginVertical: 4 }}>
      <View style={{ backgroundColor: '#1A1A2E', borderRadius: 18, borderBottomLeftRadius: 4, padding: 14, flexDirection: 'row', gap: 6, alignItems: 'center', borderWidth: 1, borderColor: '#2A2A3E' }}>
        <Dot delay={0} /><Dot delay={160} /><Dot delay={320} />
      </View>
    </Animated.View>
  );
}