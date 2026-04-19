import { useEffect } from 'react';
import { ViewStyle } from 'react-native';
import Animated, { useSharedValue, useAnimatedStyle, withRepeat, withTiming, interpolate } from 'react-native-reanimated';

export function SkeletonLoader({ height = 60, borderRadius = 12, style }: { height?: number; borderRadius?: number; style?: ViewStyle }) {
  const shimmer = useSharedValue(0);
  useEffect(() => { shimmer.value = withRepeat(withTiming(1, { duration: 1200 }), -1, true); }, []);
  const animStyle = useAnimatedStyle(() => ({ opacity: interpolate(shimmer.value, [0, 1], [0.4, 0.7]) }));
  return <Animated.View style={[{ height, borderRadius, backgroundColor: '#1A1A2E' }, animStyle, style]} />;
}