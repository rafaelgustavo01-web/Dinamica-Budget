import LogoutOutlinedIcon from '@mui/icons-material/LogoutOutlined';
import MenuOutlinedIcon from '@mui/icons-material/MenuOutlined';
import {
  AppBar,
  Box,
  Button,
  Chip,
  IconButton,
  Stack,
  Toolbar,
  Typography,
} from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '../../../features/auth/AuthProvider';
import { shortenUuid } from '../../utils/format';
import { ClientSelector } from './ClientSelector';
import {
  getRouteStatus,
  getRouteTitle,
  getStatusLabel,
} from './navigationConfig';

interface TopbarProps {
  onMenuClick: () => void;
}

export function Topbar({ onMenuClick }: TopbarProps) {
  const {
    user,
    logout,
    selectedClientId,
    setSelectedClientId,
    availableClientIds,
  } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const currentTitle = getRouteTitle(location.pathname);
  const currentStatus = getRouteStatus(location.pathname);

  return (
    <AppBar
      position="fixed"
      color="inherit"
      sx={{
        width: { lg: `calc(100% - 288px)` },
        ml: { lg: '288px' },
        backgroundColor: 'rgba(255,255,255,0.92)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid',
        borderColor: 'divider',
        boxShadow: '0 8px 24px rgba(27,42,74,0.06)',
      }}
    >
      <Toolbar
        sx={{
          minHeight: 78,
          px: { xs: 2, md: 3 },
          gap: 2,
          alignItems: 'center',
        }}
      >
        <IconButton
          color="inherit"
          edge="start"
          onClick={onMenuClick}
          sx={{ display: { lg: 'none' } }}
        >
          <MenuOutlinedIcon />
        </IconButton>

        <Box sx={{ minWidth: 0 }}>
          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.3 }}>
            <Typography variant="h5" sx={{ lineHeight: 1.2 }}>
              {currentTitle}
            </Typography>
            {currentStatus !== 'active' ? (
              <Chip
                size="small"
                label={getStatusLabel(currentStatus)}
                sx={
                  currentStatus === 'partial'
                    ? {
                        color: '#8B6209',
                        backgroundColor: '#FDF3DD',
                      }
                    : undefined
                }
              />
            ) : null}
          </Stack>
          <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 640 }}>
            {selectedClientId
              ? `Contexto de cliente ativo: ${shortenUuid(selectedClientId)}`
              : 'Selecione ou informe um cliente quando o fluxo exigir escopo.'}
          </Typography>
        </Box>

        <Box sx={{ flex: 1 }} />

        <Stack direction="row" spacing={1.5} alignItems="center">
          <ClientSelector
            isAdmin={Boolean(user?.is_admin)}
            selectedClientId={selectedClientId}
            availableClientIds={availableClientIds}
            onChange={setSelectedClientId}
          />

          {user ? (
            <Chip
              label={user.is_admin ? 'Administrador' : user.email}
              variant="outlined"
              onClick={() => navigate('/perfil')}
              sx={{
                borderColor: 'rgba(27,58,107,0.18)',
                color: 'primary.main',
                backgroundColor: 'rgba(255,255,255,0.72)',
              }}
            />
          ) : null}

          <Button
            variant="text"
            color="primary"
            startIcon={<LogoutOutlinedIcon />}
            onClick={() => void logout()}
          >
            Sair
          </Button>
        </Stack>
      </Toolbar>
    </AppBar>
  );
}
