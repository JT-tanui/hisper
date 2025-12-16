import { useEffect, useRef } from 'react';

interface Options {
  url: string;
  onMessage: (data: unknown) => void;
}

const useWebSocket = ({ url, onMessage }: Options): void => {
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const socket = new WebSocket(url);
    socketRef.current = socket;

    socket.addEventListener('message', (event) => {
      onMessage(JSON.parse(event.data));
    });

    return () => socket.close();
  }, [url, onMessage]);
};

export default useWebSocket;
