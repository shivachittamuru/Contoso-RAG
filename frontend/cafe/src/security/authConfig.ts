/*
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { LogLevel, RedirectRequest } from "@azure/msal-browser";
import appSettings from "../config/appSettings"

export const b2cPolicies = {
    names: {
        signUpSignIn: 'B2C_1_signupsignin1',
        forgotPassword: 'B2C_1_reset_v3',
        editProfile: 'B2C_1_edit_profile_v2',
    },
    authorities: {
        signUpSignIn: {
            authority: 'https://bobjacmcaps.b2clogin.com/bobjacmcaps.onmicrosoft.com/B2C_1_signupsignin1',
        },
        forgotPassword: {
            authority: 'https://bobjacmcaps.b2clogin.com/bobjacmcaps.onmicrosoft.com/B2C_1_reset_v3',
        },
        editProfile: {
            authority: 'https://bobjacmcaps.b2clogin.com/bobjacmcaps.onmicrosoft.com/b2c_1_edit_profile_v2',
        },
    },
    authorityDomain: 'bobjacmcaps.b2clogin.com',
};

/**
 * Configuration object to be passed to MSAL instance on creation. 
 * For a full list of MSAL.js configuration parameters, visit:
 * https://github.com/AzureAD/microsoft-authentication-library-for-js/blob/dev/lib/msal-browser/docs/configuration.md 
 */
export const msalConfig: any = {
    auth: {
        clientId: 'a94b4d0e-21dc-4145-af64-1d7b172beaf0',
        authority: b2cPolicies.authorities.signUpSignIn.authority,
        knownAuthorities: [b2cPolicies.authorityDomain],
        redirectUri: 'http://localhost:8000/app/', 
        postLogoutRedirectUri: 'http://localhost:8000/app/', 
        navigateToLoginRequestUrl: false,
    },
    cache: {
        cacheLocation: "sessionStorage", // This configures where your cache will be stored
        storeAuthStateInCookie: false, // Set this to "true" if you are having issues on IE11 or Edge
    },
    system: {	
        loggerOptions: {	
            loggerCallback: (level: any, message: any, containsPii: any): void => {	
                if (containsPii) {		
                    return;		
                }		
                switch (level) {		
                    case LogLevel.Error:		
                        console.error(message);		
                        return;		
                    case LogLevel.Info:		
                        console.info(message);		
                        return;		
                    case LogLevel.Verbose:		
                        console.debug(message);		
                        return;		
                    case LogLevel.Warning:		
                        console.warn(message);		
                        return;		
                }	
            }	
        }	
    }
};

export const protectedResources = {
    coffeeChat: {
        endpoint: 'ws://localhost:8000/agent/ws/chat',
        scopes: {
            read: ['https://bobjacmcaps.onmicrosoft.com/coffee/coffee.read'],
            write: ['https://bobjacmcaps.onmicrosoft.com/coffee/coffee.write'],
        },
    },
};

/**
 * Scopes you add here will be prompted for user consent during sign-in.
 * By default, MSAL.js will add OIDC scopes (openid, profile, email) to any login request.
 * For more information about OIDC scopes, visit: 
 * https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-permissions-and-consent#openid-connect-scopes
 * These values would give the app the ability to make validation calls. use on the backend
 * ["User.Read", "https://management.core.windows.net//user_impersonation"]
 */
export const loginRequest: RedirectRequest = {
    scopes: ["openid", "profile"] 
};


/**
 * Add here the scopes to request when obtaining an access token for MS Graph API. For more information, see:
 * https://github.com/AzureAD/microsoft-authentication-library-for-js/blob/dev/lib/msal-browser/docs/resources-and-scopes.md
 */
export const graphConfig: any = {
    graphMeEndpoint: "https://graph.microsoft.com/v1.0/me"
};
