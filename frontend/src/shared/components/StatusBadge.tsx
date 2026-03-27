import { Chip } from '@mui/material';

import {
  getHomologacaoLabel,
  getOrigemMatchLabel,
} from '../utils/format';

interface StatusBadgeProps {
  value: string;
  kind?: 'status' | 'origemMatch';
}

export function StatusBadge({
  value,
  kind = 'status',
}: StatusBadgeProps) {
  const label =
    kind === 'origemMatch'
      ? getOrigemMatchLabel(value as never)
      : getHomologacaoLabel(value);

  let styles = {
    color: '#1B2A4A',
    backgroundColor: 'rgba(27,58,107,0.08)',
    border: '1px solid rgba(27,58,107,0.12)',
  };

  if (['APROVADO', 'VALIDADA', 'CONSOLIDADA'].includes(value)) {
    styles = {
      color: '#155724',
      backgroundColor: '#D4EDDA',
      border: '1px solid rgba(27,122,61,0.22)',
    };
  } else if (['PENDENTE', 'SUGERIDA'].includes(value)) {
    styles = {
      color: '#856404',
      backgroundColor: '#FFF3CD',
      border: '1px solid rgba(232,166,35,0.3)',
    };
  } else if (['REPROVADO'].includes(value)) {
    styles = {
      color: '#721C24',
      backgroundColor: '#F8D7DA',
      border: '1px solid rgba(198,40,40,0.2)',
    };
  } else if (['ASSOCIACAO_DIRETA', 'PROPRIA_CLIENTE'].includes(value)) {
    styles = {
      color: '#8B6209',
      backgroundColor: '#FDF3DD',
      border: '1px solid rgba(232,166,35,0.28)',
    };
  }

  return <Chip size="small" label={label} sx={styles} />;
}
