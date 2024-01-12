import { useMsal } from '@azure/msal-react';
import { IPersonaSharedProps, Persona, PersonaSize, PersonaPresence, PersonaInitialsColor, IPersonaProps } from '@fluentui/react/lib/Persona';
import { ContextualMenu, IContextualMenuProps } from '@fluentui/react/lib/ContextualMenu';
import { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faBars } from '@fortawesome/free-solid-svg-icons'
import { IRenderFunction } from '@fluentui/react';


const Header = () => {
  const { instance, accounts } = useMsal();
  const [renderDetails, updateRenderDetails] = useState(true);
  const isAuthenticated = accounts.length > 0;
  const [showContextMenu, setShowContextMenu] = useState(false);
  const [contextMenuTarget, setContextMenuTarget] = useState<HTMLElement | null>(null);

  let activeAccount;
  if (instance) {
      activeAccount = instance.getActiveAccount();
  }

  const userName = activeAccount && activeAccount.username ? activeAccount.username : 'Unknown';
  const userInitials = userName.toUpperCase().substring(0, 2);

  const onChange = (ev: unknown, checked: boolean | undefined) => {
    updateRenderDetails(!!checked);
  };

  const adminPersona: IPersonaSharedProps = {
    imageInitials: userInitials,
    text: userName
  };

  const renderPrimaryTextHandler: IRenderFunction<IPersonaProps> = (props) => {
    return <span className='position-absolute text-white' style={{ left: 'auto', right: 50, top: 0 }}>{props?.text}</span>;
  };

  const menuItems = [
    {
      key: 'logout',
      text: 'Logout',
      iconProps: { iconName: 'SignOut' },
      onClick: () => {
        instance.logoutRedirect({ postLogoutRedirectUri: '/' });
      },
    },
  ];

  const onPersonaClick = (event: React.MouseEvent<HTMLElement, MouseEvent>) => {
    setContextMenuTarget(event.currentTarget);
    setShowContextMenu(true);
  };

  const onMenuDismiss = () => {
    setShowContextMenu(false);
  };

  const contextualMenuProps: IContextualMenuProps = {
    items: menuItems,
    target: contextMenuTarget,
    onDismiss: onMenuDismiss,
    directionalHintFixed: true,
  };

  console.log('entered Header.tsx');

  return (
    <header className="navbar navbar-dark sticky-top bg-blue flex-md-nowrap p-0">
       <a className="position-absolute btn-link" role="button"  
       style={{ left: '20px'}}
        data-bs-toggle="offcanvas" data-bs-target="#sidebar" aria-controls="sidebar">
          <FontAwesomeIcon icon={faBars} size="sm" inverse />
        </a>

      <a className="navbar-brand col-md-3 col-lg-2 me-0 px-5 pt-2 pb-2 font-weight-bold" style={{ fontSize: 15, marginLeft: '2em' }} href={'/'}>
        Contoso Coffee
      </a>
    

      <div className="collapse navbar-collapse">
      Contoso Coffee
      </div>
      <div className="navbar-nav d-flex">
        <div className="nav-item text-nowrap persona">
        {isAuthenticated && (
            <>
            <Persona
            {...adminPersona}
            text={userName}
            size={PersonaSize.size24}
            presence={PersonaPresence.none}
            hidePersonaDetails={!renderDetails}
            initialsColor={PersonaInitialsColor.gray}
            onRenderPrimaryText={renderPrimaryTextHandler}
            color='white'
            onClick={onPersonaClick}
          />
          {showContextMenu && <ContextualMenu {...contextualMenuProps} />}
          </>
        )}
        </div>
      </div>
    </header>
  )
}

export default Header;