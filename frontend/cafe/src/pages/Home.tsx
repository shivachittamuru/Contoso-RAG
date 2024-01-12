import { AuthenticatedTemplate } from "@azure/msal-react";
import { useMsal } from "@azure/msal-react";
import { Container } from "react-bootstrap";



/***
 * Component to detail ID token claims with a description for each claim. For more details on ID token claims, please check the following links:
 * ID token Claims: https://docs.microsoft.com/en-us/azure/active-directory/develop/id-tokens#claims-in-an-id-token
 * Optional Claims:  https://docs.microsoft.com/en-us/azure/active-directory/develop/active-directory-optional-claims#v10-and-v20-optional-claims-set
 */
export const Home = () => {
    console.log('inside Home.tsx');
    const { instance } = useMsal();    
    const activeAccount = instance.getActiveAccount();
    console.log(`inside Home.tsx with active account of ${activeAccount}`);

    return (
        <>
            <AuthenticatedTemplate>
                {
                    activeAccount ?
                    <Container>
                            <div>Test</div>
                    </Container>
                    :
                    null
                }
            </AuthenticatedTemplate>
        </>
    )
}