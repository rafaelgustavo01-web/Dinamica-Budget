import { Button, Paper, Stack, Typography } from '@mui/material';
import type { ReactNode } from 'react';

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: ReactNode;
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  icon,
}: EmptyStateProps) {
  return (
    <Paper
      variant="outlined"
      sx={{
        p: 4,
        borderColor: 'divider',
        background:
          'linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(237,241,248,0.8) 100%)',
      }}
    >
      <Stack spacing={1.5} alignItems="flex-start">
        {icon ? (
          <Paper
            elevation={0}
            sx={{
              width: 52,
              height: 52,
              display: 'grid',
              placeItems: 'center',
              borderRadius: 2.5,
              backgroundColor: 'rgba(27,58,107,0.08)',
              color: 'primary.main',
            }}
          >
            {icon}
          </Paper>
        ) : null}
        <Typography variant="h6">{title}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 560 }}>
          {description}
        </Typography>
        {actionLabel && onAction ? (
          <Button variant="outlined" color="primary" onClick={onAction}>
            {actionLabel}
          </Button>
        ) : null}
      </Stack>
    </Paper>
  );
}
