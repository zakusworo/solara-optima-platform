declare module 'react-plotly.js' {
  import type * as React from 'react';
  import type { Data, Layout, Config } from 'plotly.js';

  interface PlotParams {
    data: Data[];
    layout?: Partial<Layout>;
    config?: Partial<Config>;
    style?: React.CSSProperties;
    className?: string;
    onInitialized?: (figure: Readonly<{ data: Data[]; layout: Layout }>) => void;
    onUpdate?: (figure: Readonly<{ data: Data[]; layout: Layout }>) => void;
    onPurge?: () => void;
    onError?: (err: Error) => void;
    divId?: string;
    useResizeHandler?: boolean;
    debug?: boolean;
    advancedTraceType?: boolean;
  }

  export default class Plot extends React.Component<PlotParams> {}
}
