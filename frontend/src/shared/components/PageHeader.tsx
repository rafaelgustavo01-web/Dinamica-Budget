import { Box, Stack, Typography } from '@mui/material';
import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  description: string;
  actions?: ReactNode;
}

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <Stack
      direction={{ xs: 'column', md: 'row' }}
      spacing={2}
      justifyContent="space-between"
      alignItems={{ xs: 'flex-start', md: 'flex-end' }}
      sx={{ mb: 3 }}
    >
      <Box
        sx={{
          position: 'relative',
          pl: 2.25,
          '&::before': {
            content: '""',
            position: 'absolute',
            left: 0,
            top: 8,
            bottom: 8,
            width: 4,
            borderRadius: 999,
            background: 'linear-gradient(180deg, #E8A623 0%, #F0C05C 100%)',
          },
        }}
      >
        <Typography variant="h2" sx={{ mb: 0.8 }}>
          {title}
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 760 }}>
          {description}
        </Typography>
      </Box>

      {actions ? <Box>{actions}</Box> : null}
    </Stack>
  );
}
