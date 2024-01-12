import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import { AuthProvider } from './security/AuthContext';
import { BrowserRouter } from 'react-router-dom';
import { PublicClientApplication, EventType, AuthenticationResult } from "@azure/msal-browser";
import { msalConfig } from "./security/authConfig";
import './main.css';

const msalInstance = new PublicClientApplication(msalConfig);

// Default to using the first account if no account is active on page load
if (!msalInstance.getActiveAccount() && msalInstance.getAllAccounts().length > 0) {
    console.log('active account not found, setting active account');
    msalInstance.setActiveAccount(msalInstance.getAllAccounts()[0]);
}

msalInstance.addEventCallback((event) => {
  console.log('inside addEventCallback');
  if (
      (event.eventType === EventType.LOGIN_SUCCESS ||
          event.eventType === EventType.ACQUIRE_TOKEN_SUCCESS ||
          event.eventType === EventType.SSO_SILENT_SUCCESS) &&
      event.payload &&
      'account' in event.payload 
  ) {
      const payload = event.payload as AuthenticationResult;
      msalInstance.setActiveAccount(payload.account);
  }
});


ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
        <BrowserRouter>
            <App instance={msalInstance} />
        </BrowserRouter>
    </React.StrictMode>
)
