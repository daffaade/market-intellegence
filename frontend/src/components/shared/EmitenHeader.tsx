import React from 'react';
import { ArrowLeftRight } from 'lucide-react';
import type { Company, IntelligenceSnapshot } from '../../types/api';
import { formatMarketCap, formatDateTime } from '../../lib/format';
import { Button, DirectionTag, PageHeader, Tag } from '../ui/primitives';
import { WatchlistButton } from './WatchlistButton';

interface EmitenHeaderProps {
  company: Company;
  intelligence: IntelligenceSnapshot;
  section: string;
  onOpenSearch: () => void;
  isWatched: boolean;
  onToggleWatchlist: (symbol: string) => void;
}

/** Shared page header for every stock-level view. */
export const EmitenHeader: React.FC<EmitenHeaderProps> = ({
  company,
  intelligence,
  section,
  onOpenSearch,
  isWatched,
  onToggleWatchlist
}) => (
  <PageHeader
    eyebrow={
      <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
        <span>{section}</span>
        <span className="text-line-strong">/</span>
        <span>{company.sector}</span>
        <span className="text-line-strong">/</span>
        <span>{company.sub_sector}</span>
      </span>
    }
    title={
      <span className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="num">{company.symbol}</span>
        <span className="text-ink-2 font-normal text-lg">{company.name}</span>
      </span>
    }
    description={
      <span className="flex flex-wrap items-center gap-x-3 gap-y-1.5 mt-1">
        <DirectionTag direction={intelligence.direction} />
        {intelligence.is_anomaly && <Tag tone="warn">Anomali · skor {intelligence.anomaly_score}</Tag>}
        <span className="text-xs text-ink-3">
          Kap. pasar <span className="num text-ink-2">{formatMarketCap(company.market_cap)}</span>
        </span>
        <span className="text-xs text-ink-3">
          Diperbarui <span className="text-ink-2">{formatDateTime(intelligence.created_at || company.updated_at)}</span>
        </span>
      </span>
    }
    actions={
      <>
        <WatchlistButton symbol={company.symbol} isInWatchlist={isWatched} onToggle={onToggleWatchlist} withLabel />
        <Button onClick={onOpenSearch}>
          <ArrowLeftRight className="w-3.5 h-3.5" />
          Ganti emiten
        </Button>
      </>
    }
  />
);
