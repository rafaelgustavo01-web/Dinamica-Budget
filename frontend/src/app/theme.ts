import {
  createTheme,
  type PaletteMode,
  type ThemeOptions,
} from '@mui/material/styles';

const tokens = {
  primary: {
    900: '#0E1525',
    800: '#1B2A4A',
    700: '#243660',
    600: '#2D4276',
    main: '#1B3A6B',
    400: '#3A5490',
    300: '#5A7AB5',
    200: '#8AA4D0',
    100: '#B5C7E3',
    50: '#EDF1F8',
  },
  secondary: {
    dark: '#8B6209',
    main: '#E8A623',
    light: '#F0C05C',
    50: '#FDF3DD',
  },
  neutral: {
    50: '#F8F9FA',
    100: '#F1F3F5',
    200: '#E9ECEF',
    300: '#DEE2E6',
    400: '#ADB5BD',
    500: '#6C757D',
    600: '#495057',
    700: '#343A40',
    800: '#212529',
    900: '#121518',
  },
  success: {
    main: '#1B7A3D',
    light: '#D4EDDA',
    dark: '#155724',
  },
  warning: {
    main: '#E8A623',
    light: '#FFF3CD',
    dark: '#856404',
  },
  error: {
    main: '#C62828',
    light: '#F8D7DA',
    dark: '#721C24',
  },
  info: {
    main: '#1565C0',
    light: '#D1ECF1',
    dark: '#0D47A1',
  },
} as const;

const elevatedShadow =
  '0px 20px 40px rgba(27,42,74,0.14), 0px 8px 16px rgba(27,42,74,0.08)';

const customShadows = [
  'none',
  '0px 1px 3px rgba(27,42,74,0.08), 0px 1px 2px rgba(27,42,74,0.06)',
  '0px 2px 4px rgba(27,42,74,0.08), 0px 1px 3px rgba(27,42,74,0.06)',
  '0px 4px 6px rgba(27,42,74,0.08), 0px 2px 4px rgba(27,42,74,0.06)',
  '0px 6px 10px rgba(27,42,74,0.08), 0px 3px 6px rgba(27,42,74,0.06)',
  '0px 8px 16px rgba(27,42,74,0.08), 0px 4px 8px rgba(27,42,74,0.06)',
  '0px 10px 20px rgba(27,42,74,0.10), 0px 4px 8px rgba(27,42,74,0.06)',
  '0px 12px 24px rgba(27,42,74,0.10), 0px 5px 10px rgba(27,42,74,0.06)',
  '0px 14px 28px rgba(27,42,74,0.10), 0px 6px 12px rgba(27,42,74,0.06)',
  '0px 16px 32px rgba(27,42,74,0.12), 0px 6px 14px rgba(27,42,74,0.06)',
  '0px 18px 36px rgba(27,42,74,0.12), 0px 7px 16px rgba(27,42,74,0.06)',
  '0px 20px 40px rgba(27,42,74,0.12), 0px 8px 16px rgba(27,42,74,0.06)',
  elevatedShadow,
  ...Array(12).fill(elevatedShadow),
] as unknown as ThemeOptions['shadows'];

const fontFamily =
  '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
const fontFamilyDisplay = '"DM Sans", "Inter", sans-serif';

const typography: ThemeOptions['typography'] = {
  fontFamily,
  h1: {
    fontFamily: fontFamilyDisplay,
    fontSize: '2rem',
    fontWeight: 700,
    lineHeight: 1.2,
    letterSpacing: '-0.5px',
  },
  h2: {
    fontFamily: fontFamilyDisplay,
    fontSize: '1.625rem',
    fontWeight: 700,
    lineHeight: 1.25,
    letterSpacing: '-0.3px',
  },
  h3: {
    fontFamily: fontFamilyDisplay,
    fontSize: '1.375rem',
    fontWeight: 600,
    lineHeight: 1.3,
    letterSpacing: '-0.2px',
  },
  h4: {
    fontFamily,
    fontSize: '1.25rem',
    fontWeight: 600,
    lineHeight: 1.35,
    letterSpacing: '-0.1px',
  },
  h5: {
    fontFamily,
    fontSize: '1.125rem',
    fontWeight: 600,
    lineHeight: 1.4,
  },
  h6: {
    fontFamily,
    fontSize: '1rem',
    fontWeight: 600,
    lineHeight: 1.4,
    letterSpacing: '0.15px',
  },
  subtitle1: {
    fontFamily,
    fontSize: '1rem',
    fontWeight: 500,
    lineHeight: 1.5,
    letterSpacing: '0.15px',
  },
  subtitle2: {
    fontFamily,
    fontSize: '0.875rem',
    fontWeight: 500,
    lineHeight: 1.5,
    letterSpacing: '0.1px',
  },
  body1: {
    fontFamily,
    fontSize: '0.9375rem',
    fontWeight: 400,
    lineHeight: 1.6,
  },
  body2: {
    fontFamily,
    fontSize: '0.8125rem',
    fontWeight: 400,
    lineHeight: 1.55,
    letterSpacing: '0.1px',
  },
  caption: {
    fontFamily,
    fontSize: '0.75rem',
    fontWeight: 400,
    lineHeight: 1.5,
    letterSpacing: '0.4px',
  },
  overline: {
    fontFamily,
    fontSize: '0.6875rem',
    fontWeight: 600,
    lineHeight: 1.5,
    letterSpacing: '1.5px',
    textTransform: 'uppercase',
  },
  button: {
    fontFamily,
    fontSize: '0.875rem',
    fontWeight: 600,
    lineHeight: 1.15,
    letterSpacing: '0.4px',
    textTransform: 'uppercase',
  },
};

const getComponentOverrides = (_mode: PaletteMode): ThemeOptions['components'] => ({
  MuiCssBaseline: {
    styleOverrides: {
      ':root': {
        '--db-primary': tokens.primary.main,
        '--db-primary-dark': tokens.primary[800],
        '--db-primary-soft': tokens.primary[50],
        '--db-secondary': tokens.secondary.main,
        '--db-secondary-dark': tokens.secondary.dark,
        '--db-bg-default': tokens.neutral[50],
        '--db-bg-paper': '#FFFFFF',
        '--db-border': tokens.neutral[300],
        '--db-text-primary': tokens.neutral[800],
        '--db-text-secondary': tokens.neutral[600],
      },
      '*, *::before, *::after': {
        boxSizing: 'border-box',
      },
      body: {
        fontVariantNumeric: 'tabular-nums lining-nums',
      },
      '::selection': {
        backgroundColor: tokens.primary[100],
        color: tokens.primary[800],
      },
    },
  },
  MuiAppBar: {
    defaultProps: {
      elevation: 0,
      color: 'default',
    },
    styleOverrides: {
      root: {
        backgroundColor: '#FFFFFF',
        backgroundImage: 'none',
        borderBottom: `1px solid ${tokens.neutral[200]}`,
        color: tokens.neutral[800],
        boxShadow: 'none',
      },
    },
  },
  MuiDrawer: {
    styleOverrides: {
      paper: {
        backgroundColor: tokens.primary[800],
        color: '#FFFFFF',
        borderRight: 'none',
        backgroundImage:
          'linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0) 28%)',
      },
    },
  },
  MuiPaper: {
    styleOverrides: {
      root: {
        backgroundImage: 'none',
      },
      rounded: {
        borderRadius: 12,
      },
    },
  },
  MuiButton: {
    defaultProps: {
      disableElevation: true,
    },
    styleOverrides: {
      root: {
        borderRadius: 6,
        padding: '8px 20px',
        minHeight: 40,
        transition: 'all 150ms ease-in-out',
      },
      containedPrimary: {
        '&:hover': {
          backgroundColor: tokens.primary[800],
        },
      },
      containedSecondary: {
        color: tokens.primary[800],
        '&:hover': {
          backgroundColor: '#C48A1A',
        },
      },
      outlined: {
        borderWidth: 1,
        '&:hover': {
          borderWidth: 1,
        },
      },
      sizeSmall: {
        padding: '6px 14px',
        minHeight: 34,
      },
      sizeLarge: {
        padding: '10px 28px',
        minHeight: 48,
      },
    },
  },
  MuiOutlinedInput: {
    styleOverrides: {
      root: {
        borderRadius: 8,
        backgroundColor: '#FFFFFF',
        '&:hover .MuiOutlinedInput-notchedOutline': {
          borderColor: tokens.neutral[500],
        },
        '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
          borderColor: tokens.primary.main,
          borderWidth: 2,
          boxShadow: '0 0 0 3px rgba(27,58,107,0.12)',
        },
      },
      notchedOutline: {
        borderColor: tokens.neutral[400],
      },
      input: {
        padding: '12px 14px',
      },
    },
  },
  MuiInputLabel: {
    styleOverrides: {
      root: {
        color: tokens.neutral[600],
        '&.Mui-focused': {
          color: tokens.primary.main,
        },
      },
    },
  },
  MuiChip: {
    styleOverrides: {
      root: {
        borderRadius: 4,
        fontWeight: 600,
        fontSize: '0.75rem',
        letterSpacing: '0.5px',
        textTransform: 'uppercase',
        height: 24,
      },
      outlinedPrimary: {
        borderColor: tokens.primary[300],
        color: tokens.primary.main,
      },
      outlinedSecondary: {
        borderColor: tokens.secondary.main,
        color: tokens.secondary.dark,
      },
    },
  },
  MuiDialog: {
    styleOverrides: {
      paper: {
        borderRadius: 12,
        boxShadow: elevatedShadow,
      },
    },
  },
  MuiDialogTitle: {
    styleOverrides: {
      root: {
        fontFamily: fontFamilyDisplay,
        fontSize: '1.25rem',
        fontWeight: 600,
        padding: '24px 32px 16px',
      },
    },
  },
  MuiDialogContent: {
    styleOverrides: {
      root: {
        padding: '16px 32px',
      },
    },
  },
  MuiDialogActions: {
    styleOverrides: {
      root: {
        padding: '16px 32px 24px',
        gap: 12,
      },
    },
  },
  MuiTableHead: {
    styleOverrides: {
      root: {
        '& .MuiTableCell-head': {
          backgroundColor: tokens.primary[800],
          color: '#FFFFFF',
          fontWeight: 600,
          fontSize: '0.8125rem',
          letterSpacing: '0.5px',
          textTransform: 'uppercase',
          padding: '12px 16px',
          borderBottom: 'none',
          whiteSpace: 'nowrap',
        },
      },
    },
  },
  MuiTableBody: {
    styleOverrides: {
      root: {
        '& .MuiTableRow-root': {
          '&:nth-of-type(even)': {
            backgroundColor: tokens.neutral[50],
          },
          '&:hover': {
            backgroundColor: tokens.primary[50],
          },
          transition: 'background-color 100ms ease',
        },
        '& .MuiTableCell-body': {
          padding: '12px 16px',
          fontSize: '0.875rem',
          borderColor: tokens.neutral[200],
          fontVariantNumeric: 'tabular-nums lining-nums',
        },
      },
    },
  },
  MuiTableCell: {
    styleOverrides: {
      root: {
        borderColor: tokens.neutral[200],
      },
    },
  },
  MuiAlert: {
    styleOverrides: {
      root: {
        borderRadius: 8,
        padding: '14px 16px',
        fontSize: '0.875rem',
        alignItems: 'center',
      },
      standardSuccess: {
        backgroundColor: tokens.success.light,
        color: tokens.success.dark,
        borderLeft: `4px solid ${tokens.success.main}`,
        '& .MuiAlert-icon': {
          color: tokens.success.main,
        },
      },
      standardWarning: {
        backgroundColor: tokens.warning.light,
        color: tokens.warning.dark,
        borderLeft: `4px solid ${tokens.warning.main}`,
        '& .MuiAlert-icon': {
          color: tokens.warning.main,
        },
      },
      standardError: {
        backgroundColor: tokens.error.light,
        color: tokens.error.dark,
        borderLeft: `4px solid ${tokens.error.main}`,
        '& .MuiAlert-icon': {
          color: tokens.error.main,
        },
      },
      standardInfo: {
        backgroundColor: tokens.info.light,
        color: tokens.info.dark,
        borderLeft: `4px solid ${tokens.info.main}`,
        '& .MuiAlert-icon': {
          color: tokens.info.main,
        },
      },
    },
  },
  MuiTooltip: {
    styleOverrides: {
      tooltip: {
        backgroundColor: tokens.primary[800],
        color: '#FFFFFF',
        fontSize: '0.75rem',
        fontWeight: 500,
        borderRadius: 6,
        padding: '6px 12px',
      },
      arrow: {
        color: tokens.primary[800],
      },
    },
  },
  MuiTabs: {
    styleOverrides: {
      indicator: {
        height: 3,
        borderRadius: '3px 3px 0 0',
        backgroundColor: tokens.primary.main,
      },
    },
  },
  MuiTab: {
    styleOverrides: {
      root: {
        fontWeight: 600,
        fontSize: '0.875rem',
        letterSpacing: '0.3px',
        textTransform: 'uppercase',
        minHeight: 48,
        '&.Mui-selected': {
          color: tokens.primary.main,
        },
      },
    },
  },
  MuiLinearProgress: {
    styleOverrides: {
      root: {
        borderRadius: 4,
        height: 6,
        backgroundColor: tokens.neutral[200],
      },
      bar: {
        borderRadius: 4,
      },
    },
  },
  MuiDivider: {
    styleOverrides: {
      root: {
        borderColor: tokens.neutral[200],
      },
    },
  },
});

export const createDinamicaTheme = (mode: PaletteMode = 'light') =>
  createTheme({
    palette: {
      mode,
      primary: {
        main: tokens.primary.main,
        dark: tokens.primary[800],
        light: tokens.primary[300],
        contrastText: '#FFFFFF',
      },
      secondary: {
        main: tokens.secondary.main,
        dark: tokens.secondary.dark,
        light: tokens.secondary.light,
        contrastText: tokens.primary[800],
      },
      success: {
        main: tokens.success.main,
        light: tokens.success.light,
        dark: tokens.success.dark,
        contrastText: '#FFFFFF',
      },
      warning: {
        main: tokens.warning.main,
        light: tokens.warning.light,
        dark: tokens.warning.dark,
        contrastText: tokens.primary[800],
      },
      error: {
        main: tokens.error.main,
        light: tokens.error.light,
        dark: tokens.error.dark,
        contrastText: '#FFFFFF',
      },
      info: {
        main: tokens.info.main,
        light: tokens.info.light,
        dark: tokens.info.dark,
        contrastText: '#FFFFFF',
      },
      background: {
        default: tokens.neutral[50],
        paper: '#FFFFFF',
      },
      text: {
        primary: tokens.neutral[800],
        secondary: tokens.neutral[600],
        disabled: tokens.neutral[500],
      },
      divider: tokens.neutral[300],
      action: {
        hover: 'rgba(27,42,74,0.04)',
        selected: 'rgba(27,42,74,0.08)',
        disabled: tokens.neutral[400],
        disabledBackground: tokens.neutral[200],
      },
    },
    typography,
    spacing: 8,
    shape: {
      borderRadius: 8,
    },
    shadows: customShadows,
    components: getComponentOverrides(mode),
  });

export const appTheme = createDinamicaTheme('light');
