import React from 'react';
import { Hero } from './Hero';
import { IntentRouteChat } from './IntentRouteChat';
import './index.css';

function App() {
  return (
    <div style={{ width: '100%', minHeight: '100vh' }}>
      <Hero />
      <IntentRouteChat />
    </div>
  );
}

export default App;
