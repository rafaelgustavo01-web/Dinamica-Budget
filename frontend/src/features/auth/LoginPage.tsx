import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { useLocation, useNavigate } from 'react-router-dom';
import { z } from 'zod';

import { useAuth } from './AuthProvider';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';

const loginSchema = z.object({
  email: z.email('Informe um email válido.'),
  password: z.string().min(1, 'Informe a senha.'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export function LoginPage() {
  const { login } = useAuth();
  const { showMessage } = useFeedback();
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = (location.state as { from?: string } | null)?.from ?? '/dashboard';

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      showMessage('Sessão iniciada com sucesso.');
      navigate(redirectTo, { replace: true });
    },
  });

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', lg: '1.15fr 0.85fr' },
        background:
          'linear-gradient(135deg, #1B2A4A 0%, #1B3A6B 46%, #F8F9FA 46%, #F8F9FA 100%)',
      }}
    >
      <Box
        sx={{
          position: 'relative',
          overflow: 'hidden',
          display: 'flex',
          alignItems: 'flex-end',
          px: { xs: 3, md: 6 },
          py: { xs: 4, md: 6 },
          '&::before': {
            content: '""',
            position: 'absolute',
            right: { xs: -88, md: -56 },
            top: { xs: 36, md: 64 },
            width: { xs: 180, md: 260 },
            height: { xs: 180, md: 260 },
            borderRadius: 10,
            border: '18px solid rgba(255,255,255,0.08)',
            transform: 'rotate(45deg)',
          },
          '&::after': {
            content: '""',
            position: 'absolute',
            left: { xs: -56, md: -16 },
            top: { xs: -40, md: -20 },
            width: 180,
            height: 180,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(232,166,35,0.32), transparent 70%)',
          },
        }}
      >
        <Stack spacing={2.5} sx={{ maxWidth: 560, color: 'common.white', position: 'relative' }}>
          <Box
            sx={{
              width: 64,
              height: 6,
              borderRadius: 999,
              background: 'linear-gradient(90deg, #E8A623 0%, #F0C05C 100%)',
            }}
          />
          <Typography variant="overline" sx={{ color: 'rgba(255,255,255,0.7)' }}>
            Construtora Dinâmica
          </Typography>
          <Typography variant="h1" sx={{ fontSize: { xs: '2.2rem', md: '3.6rem' } }}>
            Dinâmica Budget para operação orçamentária com rastreabilidade e controle.
          </Typography>
          <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.78)' }}>
            Catálogo, busca inteligente, homologação, composições e governança por cliente em
            uma interface interna preparada para intranet corporativa.
          </Typography>
          <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.62)', maxWidth: 480 }}>
            Acesso seguro, integração direta com o backend oficial e experiência operacional
            objetiva para o time interno.
          </Typography>
        </Stack>
      </Box>

      <Box
        sx={{
          display: 'grid',
          placeItems: 'center',
          px: 3,
          py: 4,
        }}
      >
        <Paper
          sx={{
            width: '100%',
            maxWidth: 460,
            p: { xs: 3, md: 4 },
            border: '1px solid rgba(27,58,107,0.08)',
            boxShadow: '0 24px 48px rgba(27,42,74,0.12)',
          }}
        >
          <Stack spacing={3}>
            <Stack direction="row" spacing={1.5} alignItems="center">
              <Box
                sx={{
                  width: 44,
                  height: 44,
                  borderRadius: 2.5,
                  display: 'grid',
                  placeItems: 'center',
                  background:
                    'linear-gradient(135deg, rgba(27,58,107,1) 0%, rgba(36,54,96,1) 100%)',
                  color: 'common.white',
                  boxShadow: '0 10px 20px rgba(27,58,107,0.18)',
                }}
              >
                <LockOutlinedIcon />
              </Box>
              <div>
                <Typography variant="h5">Acessar sistema</Typography>
                <Typography variant="body2" color="text.secondary">
                  Autenticação integrada ao backend oficial.
                </Typography>
              </div>
            </Stack>

            {loginMutation.isError ? (
              <Alert severity="error">
                {extractApiErrorMessage(
                  loginMutation.error,
                  'Não foi possível autenticar no momento.',
                )}
              </Alert>
            ) : null}

            <Stack
              component="form"
              spacing={2}
              onSubmit={handleSubmit((values) => loginMutation.mutate(values))}
            >
              <TextField
                label="Email"
                type="email"
                autoComplete="username"
                error={Boolean(errors.email)}
                helperText={errors.email?.message}
                {...register('email')}
              />
              <TextField
                label="Senha"
                type="password"
                autoComplete="current-password"
                error={Boolean(errors.password)}
                helperText={errors.password?.message}
                {...register('password')}
              />

              <Button
                type="submit"
                variant="contained"
                size="large"
                disabled={loginMutation.isPending}
              >
                {loginMutation.isPending ? (
                  <CircularProgress size={20} color="inherit" />
                ) : (
                  'Entrar'
                )}
              </Button>
            </Stack>
          </Stack>
        </Paper>
      </Box>
    </Box>
  );
}
