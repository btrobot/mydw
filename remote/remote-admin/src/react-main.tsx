import React from 'react';
import ReactDOM from 'react-dom/client';

import { AppProviders } from './app/providers.js';

const root = document.getElementById('app');

if (!root) {
  throw new Error('Missing #app root element for remote-admin React shell');
}

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <AppProviders />
  </React.StrictMode>
);
