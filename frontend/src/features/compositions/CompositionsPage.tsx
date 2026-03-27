import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  InputAdornment,
  List,
  ListItemButton,
  ListItemText,
  Paper,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { useAuth } from '../auth/AuthProvider';
import { DataTable } from '../../shared/components/DataTable';
import { EmptyState } from '../../shared/components/EmptyState';
import { PageHeader } from '../../shared/components/PageHeader';
import { composicoesApi } from '../../shared/services/api/composicoesApi';
import { servicesApi } from '../../shared/services/api/servicesApi';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import type { ServicoTcpoResponse } from '../../shared/types/contracts/servicos';
import { hasClientePerfil } from '../../shared/utils/permissions';
import { formatCurrency } from '../../shared/utils/format';

export function CompositionsPage() {
  const { user, selectedClientId } = useAuth();
  const queryClient = useQueryClient();

  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedService, setSelectedService] = useState<ServicoTcpoResponse | null>(null);

  // Clone dialog state
  const [cloneOpen, setCloneOpen] = useState(false);
  const [cloneCode, setCloneCode] = useState('');
  const [cloneDesc, setCloneDesc] = useState('');

  // Add component dialog state
  const [addOpen, setAddOpen] = useState(false);
  const [addSearch, setAddSearch] = useState('');
  const [addSearchPage] = useState(1);
  const [selectedComponent, setSelectedComponent] = useState<ServicoTcpoResponse | null>(null);
  const [addQty, setAddQty] = useState('1');

  const canEdit =
    Boolean(selectedClientId) &&
    (user?.is_admin ||
      hasClientePerfil(user, selectedClientId, ['APROVADOR', 'ADMIN']));

  const isOwnedByClient =
    selectedService?.origem === 'PROPRIA' &&
    selectedService?.cliente_id === selectedClientId;

  const servicesQuery = useQuery({
    queryKey: ['composition-page', selectedClientId, query, page, pageSize],
    queryFn: () =>
      servicesApi.list({
        page,
        page_size: pageSize,
        q: query || undefined,
        cliente_id: selectedClientId || undefined,
      }),
    enabled: Boolean(user && (selectedClientId || user.is_admin)),
  });

  const compositionQuery = useQuery({
    queryKey: ['composition-page', 'composition', selectedService?.id],
    queryFn: () => servicesApi.getComposicao(selectedService!.id),
    enabled: Boolean(selectedService?.id),
  });

  // Search query for add-component dialog
  const componentSearchQuery = useQuery({
    queryKey: ['composition-page', 'component-search', addSearch, addSearchPage],
    queryFn: () =>
      servicesApi.list({
        page: addSearchPage,
        page_size: 10,
        q: addSearch || undefined,
        cliente_id: selectedClientId || undefined,
      }),
    enabled: addOpen,
  });

  const cloneMutation = useMutation({
    mutationFn: () =>
      composicoesApi.clonar({
        servico_origem_id: selectedService!.id,
        cliente_id: selectedClientId,
        codigo_clone: cloneCode,
        descricao: cloneDesc || undefined,
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['composition-page'] });
      setSelectedService(data.servico);
      setCloneOpen(false);
      setCloneCode('');
      setCloneDesc('');
    },
  });

  const addComponentMutation = useMutation({
    mutationFn: () =>
      composicoesApi.adicionarComponente(selectedService!.id, {
        insumo_filho_id: selectedComponent!.id,
        quantidade_consumo: Number(addQty),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['composition-page', 'composition', selectedService?.id],
      });
      setAddOpen(false);
      setAddSearch('');
      setSelectedComponent(null);
      setAddQty('1');
    },
  });

  const removeComponentMutation = useMutation({
    mutationFn: (componenteId: string) =>
      composicoesApi.removerComponente(selectedService!.id, componenteId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['composition-page', 'composition', selectedService?.id],
      });
    },
  });

  if (!selectedClientId && !user?.is_admin) {
    return (
      <>
        <PageHeader
          title="Composições"
          description="Visualização operacional da estrutura pai-filho de serviços."
        />
        <EmptyState
          title="Selecione um cliente para consultar o catálogo visível"
          description="O frontend mantém o recorte por cliente para evitar consumo fora do escopo do usuário."
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Composições"
        description="Visualize a estrutura pai-filho de serviços e gerencie composições do catálogo próprio."
      />

      <Stack direction={{ xs: 'column', xl: 'row' }} spacing={2}>
        <Paper sx={{ flex: 1, p: 3 }}>
          <TextField
            fullWidth
            label="Buscar serviço"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(1);
            }}
            sx={{ mb: 2 }}
          />

          {servicesQuery.isError ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              {extractApiErrorMessage(
                servicesQuery.error,
                'Falha ao carregar serviços para composição.',
              )}
            </Alert>
          ) : null}

          <DataTable
            columns={[
              { key: 'codigo', header: 'Código', render: (row) => row.codigo_origem },
              { key: 'descricao', header: 'Descrição', render: (row) => row.descricao },
              { key: 'unidade', header: 'Unidade', render: (row) => row.unidade_medida },
              {
                key: 'custo',
                header: 'Custo',
                align: 'right',
                render: (row) => formatCurrency(row.custo_unitario),
              },
            ]}
            rows={servicesQuery.data?.items ?? []}
            rowKey={(row) => row.id}
            loading={servicesQuery.isLoading}
            page={page}
            pageSize={pageSize}
            total={servicesQuery.data?.total ?? 0}
            emptyTitle="Nenhum serviço disponível"
            emptyDescription="A composição só pode ser aberta para itens retornados pelo catálogo visível."
            onPageChange={setPage}
            onPageSizeChange={(value) => {
              setPageSize(value);
              setPage(1);
            }}
            onRowClick={(row) => setSelectedService(row)}
          />
        </Paper>

        <Stack spacing={2} sx={{ flex: 0.9 }}>
          <Paper sx={{ p: 3 }}>
            <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1.5 }}>
              <Typography variant="h6">Explosão da composição</Typography>
              {selectedService && canEdit && (
                <Stack direction="row" spacing={1}>
                  <Tooltip title="Clonar para meu catálogo">
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<ContentCopyIcon />}
                      onClick={() => setCloneOpen(true)}
                    >
                      Clonar
                    </Button>
                  </Tooltip>
                  {isOwnedByClient && (
                    <Tooltip title="Adicionar componente">
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<AddIcon />}
                        onClick={() => setAddOpen(true)}
                      >
                        Componente
                      </Button>
                    </Tooltip>
                  )}
                </Stack>
              )}
            </Stack>

            {compositionQuery.isError ? (
              <Alert severity="error" sx={{ mb: 1 }}>
                {extractApiErrorMessage(compositionQuery.error, 'Falha ao carregar composição.')}
              </Alert>
            ) : null}

            {cloneMutation.isError ? (
              <Alert severity="error" sx={{ mb: 1 }}>
                {extractApiErrorMessage(cloneMutation.error, 'Falha ao clonar composição.')}
              </Alert>
            ) : null}

            {addComponentMutation.isError ? (
              <Alert severity="error" sx={{ mb: 1 }}>
                {extractApiErrorMessage(addComponentMutation.error, 'Falha ao adicionar componente.')}
              </Alert>
            ) : null}

            {removeComponentMutation.isError ? (
              <Alert severity="error" sx={{ mb: 1 }}>
                {extractApiErrorMessage(removeComponentMutation.error, 'Falha ao remover componente.')}
              </Alert>
            ) : null}

            {selectedService ? (
              compositionQuery.data ? (
                <Stack spacing={1.5}>
                  <Typography variant="subtitle1">{selectedService.descricao}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Custo total da composição:{' '}
                    {formatCurrency(compositionQuery.data.custo_total_composicao)}
                  </Typography>
                  {compositionQuery.data.itens.length ? (
                    compositionQuery.data.itens.map((item) => (
                      <Paper key={item.id} variant="outlined" sx={{ p: 1.5 }}>
                        <Stack direction="row" alignItems="flex-start" justifyContent="space-between">
                          <Stack spacing={0.25}>
                            <Typography variant="body2">{item.descricao_filho}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {item.quantidade_consumo} {item.unidade_medida} ·{' '}
                              {formatCurrency(item.custo_total)}
                            </Typography>
                          </Stack>
                          {isOwnedByClient && canEdit && (
                            <Tooltip title="Remover componente">
                              <IconButton
                                size="small"
                                onClick={() => removeComponentMutation.mutate(item.id)}
                                disabled={removeComponentMutation.isPending}
                              >
                                <DeleteOutlineIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                        </Stack>
                      </Paper>
                    ))
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      Este item não possui componentes cadastrados.
                    </Typography>
                  )}
                </Stack>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Selecione um serviço para carregar a composição.
                </Typography>
              )
            ) : (
              <Typography variant="body2" color="text.secondary">
                Escolha um serviço na lista para visualizar os componentes.
              </Typography>
            )}
          </Paper>
        </Stack>
      </Stack>

      {/* Clone dialog */}
      <Dialog open={cloneOpen} onClose={() => setCloneOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Clonar composição para meu catálogo</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Código do clone"
              value={cloneCode}
              onChange={(e) => setCloneCode(e.target.value)}
              required
              fullWidth
              helperText="Código único para identificar o novo item no seu catálogo."
            />
            <TextField
              label="Descrição (opcional)"
              value={cloneDesc}
              onChange={(e) => setCloneDesc(e.target.value)}
              fullWidth
              helperText="Se omitido, herda a descrição do original."
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCloneOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            disabled={!cloneCode.trim() || cloneMutation.isPending}
            onClick={() => cloneMutation.mutate()}
          >
            Clonar
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add component dialog */}
      <Dialog open={addOpen} onClose={() => setAddOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Adicionar componente</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Buscar insumo"
              value={addSearch}
              onChange={(e) => setAddSearch(e.target.value)}
              fullWidth
              InputProps={{
                endAdornment: componentSearchQuery.isLoading ? (
                  <InputAdornment position="end">…</InputAdornment>
                ) : null,
              }}
            />
            {componentSearchQuery.data?.items.length ? (
              <Paper variant="outlined" sx={{ maxHeight: 200, overflow: 'auto' }}>
                <List dense disablePadding>
                  {componentSearchQuery.data.items.map((svc) => (
                    <ListItemButton
                      key={svc.id}
                      selected={selectedComponent?.id === svc.id}
                      onClick={() => setSelectedComponent(svc)}
                    >
                      <ListItemText
                        primary={svc.descricao}
                        secondary={`${svc.codigo_origem} · ${svc.unidade_medida} · ${formatCurrency(svc.custo_unitario)}`}
                      />
                    </ListItemButton>
                  ))}
                </List>
              </Paper>
            ) : null}
            <TextField
              label="Quantidade de consumo"
              type="number"
              value={addQty}
              onChange={(e) => setAddQty(e.target.value)}
              fullWidth
              inputProps={{ min: 0.0001, step: 'any' }}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            disabled={!selectedComponent || !addQty || Number(addQty) <= 0 || addComponentMutation.isPending}
            onClick={() => addComponentMutation.mutate()}
          >
            Adicionar
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
