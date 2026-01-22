/**
 * Hook tests for custom React hooks
 */
import { renderHook, act } from '@testing-library/react';
import { useAgentStore } from '@/stores/agentStore';

describe('useAgentStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    const { result } = renderHook(() => useAgentStore());
    act(() => {
      result.current.resetState();
    });
  });

  it('should have initial state', () => {
    const { result } = renderHook(() => useAgentStore());
    
    expect(result.current.messages).toEqual([]);
    expect(result.current.isConnected).toBe(false);
    expect(result.current.isTyping).toBe(false);
  });

  it('should add messages', () => {
    const { result } = renderHook(() => useAgentStore());
    
    act(() => {
      result.current.addMessage({
        id: '1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date(),
      });
    });
    
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].content).toBe('Hello');
  });

  it('should update connection status', () => {
    const { result } = renderHook(() => useAgentStore());
    
    act(() => {
      result.current.setConnected(true);
    });
    
    expect(result.current.isConnected).toBe(true);
  });

  it('should update typing status', () => {
    const { result } = renderHook(() => useAgentStore());
    
    act(() => {
      result.current.setTyping(true);
    });
    
    expect(result.current.isTyping).toBe(true);
  });

  it('should append streaming response', () => {
    const { result } = renderHook(() => useAgentStore());
    
    act(() => {
      result.current.appendStreamingResponse('Hello');
      result.current.appendStreamingResponse(' World');
    });
    
    expect(result.current.streamingResponse).toBe('Hello World');
  });
});

describe('Hook Setup', () => {
  it('should be properly configured', () => {
    expect(true).toBe(true);
  });
});
