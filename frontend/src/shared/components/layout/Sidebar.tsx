import {
  Box,
  Chip,
  Divider,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Typography,
} from '@mui/material';
import { NavLink, useLocation } from 'react-router-dom';

import { useAuth } from '../../../features/auth/AuthProvider';
import {
  getNavigationStatusLabel,
  navigationItems,
} from './navigationConfig';

export const drawerWidth = 288;

interface SidebarProps {
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export function Sidebar({ mobileOpen, onMobileClose }: SidebarProps) {
  const { user } = useAuth();
  const location = useLocation();
  const groups = ['Operação', 'Governança', 'Conta'] as const;

  const content = (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          right: -64,
          top: 76,
          width: 220,
          height: 220,
          borderRadius: 8,
          border: '18px solid rgba(255,255,255,0.05)',
          transform: 'rotate(45deg)',
          pointerEvents: 'none',
        },
        '&::after': {
          content: '""',
          position: 'absolute',
          right: 12,
          top: 126,
          width: 120,
          height: 120,
          borderRadius: 8,
          border: '12px solid rgba(232,166,35,0.12)',
          transform: 'rotate(45deg)',
          pointerEvents: 'none',
        },
      }}
    >
      <Box sx={{ px: 3, py: 3.5, position: 'relative', zIndex: 1 }}>
        <Stack direction="row" spacing={1.5} alignItems="stretch">
          <Box
            sx={{
              width: 6,
              borderRadius: 999,
              background: 'linear-gradient(180deg, #E8A623 0%, #F0C05C 100%)',
              boxShadow: '0 0 0 1px rgba(255,255,255,0.06)',
            }}
          />
          <Box>
            <Typography variant="overline" sx={{ color: 'rgba(255,255,255,0.64)' }}>
              Construtora Dinâmica
            </Typography>
            <Typography variant="h4" sx={{ color: 'common.white', mt: 0.25 }}>
              Budget
            </Typography>
            <Typography
              variant="body2"
              sx={{ mt: 1.25, maxWidth: 212, color: 'rgba(255,255,255,0.78)' }}
            >
              Sistema interno para catálogo, busca, homologação e governança por cliente.
            </Typography>
          </Box>
        </Stack>
      </Box>

      <Divider sx={{ borderColor: 'rgba(255,255,255,0.08)' }} />

      <Box sx={{ flex: 1, overflowY: 'auto', px: 2, py: 2 }}>
        {groups.map((group) => {
          const items = navigationItems.filter(
            (item) => item.group === group && item.visible(user) && item.showInMenu !== false,
          );

          if (!items.length) {
            return null;
          }

          return (
            <Box key={group} sx={{ mb: 2.5 }}>
              <Typography
                variant="caption"
                sx={{
                  px: 1.5,
                  textTransform: 'uppercase',
                  color: 'rgba(255,255,255,0.42)',
                  letterSpacing: '0.08em',
                }}
              >
                {group}
              </Typography>

              <List sx={{ mt: 1, py: 0 }}>
                {items.map((item) => {
                  const active =
                    location.pathname === item.path ||
                    location.pathname.startsWith(`${item.path}/`);

                  return (
                    <ListItemButton
                      key={item.path}
                      component={NavLink}
                      to={item.path}
                      onClick={onMobileClose}
                      sx={{
                        borderRadius: 2.5,
                        mb: 0.5,
                        pl: 1.25,
                        borderLeft: active ? '3px solid #E8A623' : '3px solid transparent',
                        color: active ? '#ffffff' : 'rgba(255,255,255,0.82)',
                        backgroundColor: active
                          ? 'rgba(232,166,35,0.14)'
                          : 'transparent',
                        '&:hover': {
                          backgroundColor: active
                            ? 'rgba(232,166,35,0.18)'
                            : 'rgba(255,255,255,0.06)',
                        },
                      }}
                    >
                      <ListItemIcon sx={{ color: 'inherit', minWidth: 36 }}>
                        {item.icon}
                      </ListItemIcon>
                      <ListItemText
                        primary={item.label}
                        primaryTypographyProps={{ fontSize: 14, fontWeight: 500 }}
                      />
                      {item.status !== 'active' ? (
                        <Chip
                          size="small"
                          label={getNavigationStatusLabel(item)}
                          sx={{
                            ml: 1,
                            color:
                              item.status === 'partial' ? '#8B6209' : 'rgba(255,255,255,0.72)',
                            backgroundColor:
                              item.status === 'partial'
                                ? '#FDF3DD'
                                : 'rgba(255,255,255,0.12)',
                          }}
                        />
                      ) : null}
                    </ListItemButton>
                  );
                })}
              </List>
            </Box>
          );
        })}
      </Box>

      <Stack
        spacing={0.5}
        sx={{
          px: 3,
          py: 2.5,
          borderTop: '1px solid rgba(255,255,255,0.08)',
          color: 'rgba(255,255,255,0.72)',
        }}
      >
        <Typography variant="body2">Ambiente interno</Typography>
        <Typography variant="caption">
          Navegação adaptada às permissões do usuário e ao backend operacional disponível.
        </Typography>
      </Stack>
    </Box>
  );

  return (
    <>
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={onMobileClose}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', lg: 'none' },
          '& .MuiDrawer-paper': { width: drawerWidth },
        }}
      >
        {content}
      </Drawer>

      <Drawer
        variant="permanent"
        open
        sx={{
          display: { xs: 'none', lg: 'block' },
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        {content}
      </Drawer>
    </>
  );
}
