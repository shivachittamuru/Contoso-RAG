import { BrowserRouter, useNavigate} from 'react-router-dom';
//import MainRoutes from './routes/MainRoutes';

import { useEffect } from 'react';
import { Routes, Route } from "react-router-dom";
import { AuthenticatedTemplate, MsalProvider, UnauthenticatedTemplate, useMsal } from '@azure/msal-react';
import { AuthenticationResult, EventType, IPublicClientApplication } from '@azure/msal-browser';

import { PageLayout } from './components/PageLayout';
import { Home } from './pages/Home';
import { b2cPolicies, protectedResources } from './security/authConfig';
import { compareIssuingPolicy } from './utils/claimUtils';
import MainLayout from './layout/MainLayout';
import ChatInterface from './views/ChatInterface';
import LoginPage from './views/LoginPage';

interface IdTokenClaims {
  oid?: string;  
  sub?: string;  
  tfp?: string;  
}

interface AppProps {
  instance: IPublicClientApplication;
}

const Pages = () => {
  /**
   * useMsal is hook that returns the PublicClientApplication instance,
   * an array of all accounts currently signed in and an inProgress value
   * that tells you what msal is currently doing. For more, visit:
   * https://github.com/AzureAD/microsoft-authentication-library-for-js/blob/dev/lib/msal-react/docs/hooks.md
   */

  console.log('inside Pages');
  const navigate = useNavigate();
  const { instance } = useMsal();
  console.log('instance: ', instance);

  useEffect(() => {
    console.log('inside useEffect of Pages');
    
      const callbackId = instance.addEventCallback((event) => {
        console.log('inside addEventCallback');
        if ((event.eventType === EventType.LOGIN_SUCCESS || event.eventType === EventType.ACQUIRE_TOKEN_SUCCESS ||
          event.eventType === EventType.SSO_SILENT_SUCCESS) && event.payload && 'account' in event.payload) 
          {
            const authenticationResult = event.payload as AuthenticationResult;
            const claims = authenticationResult.idTokenClaims as IdTokenClaims;
            if (authenticationResult.account && claims.oid && claims.sub) {
              /**
               * For the purpose of setting an active account for UI update, we want to consider only the auth
               * response resulting from SUSI flow. "tfp" claim in the id token tells us the policy (NOTE: legacy
               * policies may use "acr" instead of "tfp"). To learn more about B2C tokens, visit:
               * https://docs.microsoft.com/en-us/azure/active-directory-b2c/tokens-overview
               */
              if (compareIssuingPolicy(authenticationResult.idTokenClaims, b2cPolicies.names.editProfile)) {
                // retrieve the account from initial sing-in to the app
                const originalSignInAccount = instance
                    .getAllAccounts()
                    .find(
                        (account) =>
                            account?.idTokenClaims &&
                            account?.idTokenClaims?.oid === claims.oid &&
                            account?.idTokenClaims?.sub === claims.sub && 
                            compareIssuingPolicy(account.idTokenClaims, b2cPolicies.names.signUpSignIn)        
                    );

                const signUpSignInFlowRequest = {
                    authority: b2cPolicies.authorities.signUpSignIn.authority,
                    account: originalSignInAccount,
                };

                // silently login again with the signUpSignIn policy
                instance.ssoSilent(signUpSignInFlowRequest);
            }

            /**
             * Below we are checking if the user is returning from the reset password flow.
             * If so, we will ask the user to reauthenticate with their new password.
             * If you do not want this behavior and prefer your users to stay signed in instead,
             * you can replace the code below with the same pattern used for handling the return from
             * profile edit flow
             */
            if (compareIssuingPolicy(authenticationResult.idTokenClaims, b2cPolicies.names.forgotPassword)) {
                const signUpSignInFlowRequest = {
                    authority: b2cPolicies.authorities.signUpSignIn.authority,
                    scopes: [
                        ...protectedResources.coffeeChat.scopes.read,
                        ...protectedResources.coffeeChat.scopes.write,
                    ],
                };
                instance.loginRedirect(signUpSignInFlowRequest);
            }
        }
        navigate('/app');
      }



      if (event.eventType === EventType.LOGIN_FAILURE) {
        // Check for forgot password error
        // Learn more about AAD error codes at https://docs.microsoft.com/en-us/azure/active-directory/develop/reference-aadsts-error-codes
        if (event.error && 'errorMessage' in event.error && event.error.errorMessage.includes('AADB2C90118')) {
            const resetPasswordRequest = {
                authority: b2cPolicies.authorities.forgotPassword.authority,
                scopes: [],
            };
            instance.loginRedirect(resetPasswordRequest);
        }
      }  
      });

      return () => {
        console.log('inside return of useEffect of Pages');
          if (callbackId) {
              instance.removeEventCallback(callbackId);
          }
      };
      // eslint-disable-next-line
  }, [instance]);

  return (

      <PageLayout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/app" element={<MainLayout />}>
            <Route
              index
              element={
                <>
                  <AuthenticatedTemplate>
                    <ChatInterface />
                  </AuthenticatedTemplate>
                  <UnauthenticatedTemplate>
                    <LoginPage />
                  </UnauthenticatedTemplate>
                </>
              }
            />
          </Route>
          <Route path="/postlogin" element={<MainLayout />}>
            <Route
              index
              element={
                <>
                  <AuthenticatedTemplate>
                    <ChatInterface />
                  </AuthenticatedTemplate>
                  <UnauthenticatedTemplate>
                    <LoginPage />
                  </UnauthenticatedTemplate>
                </>
              }
            />
          </Route>
          <Route
              path="*"
              element={
                <UnauthenticatedTemplate>
                  <div>Please login to access this page.</div>
                </UnauthenticatedTemplate>
              }
            />
        </Routes>
      </PageLayout>

  );
};

export default function App({ instance }: AppProps) {
  console.log('inside App');
  return (
    <MsalProvider instance={instance}>
      <Pages /> 
    </MsalProvider>
  );
}
