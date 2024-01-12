import { AuthenticatedTemplate } from "@azure/msal-react";
// import { NavigationBar } from "./NavigationBar";

export const PageLayout: React.FC<React.PropsWithChildren<object>> = (props) => {
    return (
        <>
            {/* <NavigationBar />
            <br /> */}
            {props.children}
            <AuthenticatedTemplate>
                <footer>
                    <center>
                        How did we do?
                        <a
                            rel="noopener"
                            href="https://forms.office.com/Pages/ResponsePage.aspx?id=v4j5cvGGr0GRqy180BHbR73pcsbpbxNJuZCMKN0lURpUMlRHSkc5U1NLUkxFNEtVN0dEOTFNQkdTWiQlQCN0PWcu"
                            target="_blank"
                        >
                            {' '}
                            Share your experience!
                        </a>
                    </center>
                </footer>
            </AuthenticatedTemplate>
        </>
    );
}