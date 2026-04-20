import { useEffect, useRef } from "react";
import { createChart, ColorType, IChartApi, ISeriesApi, LineStyle, Time } from "lightweight-charts";
import type { Signal, Bar } from "../types";

interface Props {
  bars: Bar[];
  signal?: Signal | null;
}

export default function TradingViewChart({ bars, signal }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeRef = useRef<ISeriesApi<"Histogram"> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#14171f" },
        textColor: "#e6e8ee",
      },
      grid: {
        vertLines: { color: "#1d2230" },
        horzLines: { color: "#1d2230" },
      },
      rightPriceScale: { borderColor: "#262b38" },
      timeScale: { borderColor: "#262b38", timeVisible: true, secondsVisible: false },
      crosshair: { mode: 1 },
      autoSize: true,
    });
    chartRef.current = chart;

    const candles = chart.addCandlestickSeries({
      upColor: "#3ddc97",
      downColor: "#ff6b6b",
      wickUpColor: "#3ddc97",
      wickDownColor: "#ff6b6b",
      borderVisible: false,
    });
    candleRef.current = candles;

    const volume = chart.addHistogramSeries({
      color: "#26a69a",
      priceFormat: { type: "volume" },
      priceScaleId: "",
    });
    volume.priceScale().applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });
    volumeRef.current = volume;

    return () => {
      chart.remove();
      chartRef.current = null;
      candleRef.current = null;
      volumeRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!candleRef.current || !volumeRef.current) return;
    const candles = candleRef.current;
    const volume = volumeRef.current;

    const cdata = bars.map(b => ({
      time: (b.date.slice(0, 10)) as Time,
      open: b.open, high: b.high, low: b.low, close: b.close,
    }));
    candles.setData(cdata);
    volume.setData(
      bars.map(b => ({
        time: (b.date.slice(0, 10)) as Time,
        value: b.volume,
        color: b.close >= b.open ? "rgba(61,220,151,0.35)" : "rgba(255,107,107,0.35)",
      }))
    );

    // Clear prior price lines
    // @ts-ignore — removePriceLine requires instance, we recreate below
    candles._linesCache?.forEach?.((pl: any) => candles.removePriceLine(pl));
    (candles as any)._linesCache = [];

    if (signal) {
      const add = (price: number, title: string, color: string, style: LineStyle = LineStyle.Dashed) => {
        const pl = candles.createPriceLine({
          price,
          color,
          lineStyle: style,
          lineWidth: 2,
          title,
          axisLabelVisible: true,
        });
        (candles as any)._linesCache.push(pl);
      };
      if (signal.buy_low != null)  add(signal.buy_low,  "Entry ↓", "#3ddc97");
      if (signal.buy_high != null) add(signal.buy_high, "Entry ↑", "#3ddc97");
      if (signal.sell_low != null)  add(signal.sell_low,  "Exit ↓",  "#f4bf4f");
      if (signal.sell_high != null) add(signal.sell_high, "Exit ↑",  "#f4bf4f");
      if (signal.stop_loss != null) add(signal.stop_loss, "Stop",    "#ff6b6b", LineStyle.Solid);

      // Signal marker on last bar
      if (cdata.length > 0) {
        const last = cdata[cdata.length - 1];
        const markerColor =
          signal.action === "BUY" ? "#3ddc97" :
          signal.action === "SELL" ? "#ff6b6b" : "#c0c0c0";
        candles.setMarkers([{
          time: last.time,
          position: signal.action === "SELL" ? "aboveBar" : "belowBar",
          color: markerColor,
          shape: signal.action === "SELL" ? "arrowDown" : signal.action === "BUY" ? "arrowUp" : "circle",
          text: `${signal.action} ${(signal.confidence * 100).toFixed(0)}%`,
        }]);
      }
    } else {
      candles.setMarkers([]);
    }

    chartRef.current?.timeScale().fitContent();
  }, [bars, signal]);

  return (
    <div className="chart-wrapper">
      <div ref={containerRef} style={{ width: "100%", height: "100%" }} />
    </div>
  );
}
