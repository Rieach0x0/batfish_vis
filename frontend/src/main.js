/**
 * Application entry point.
 *
 * Initializes the Batfish Visualization application.
 */

import initApp from './App.js';
import './styles.css';

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', () => {
  console.log('Batfish Visualization App starting...');

  // Initialize application
  initApp();

  console.log('App initialized successfully');
});
