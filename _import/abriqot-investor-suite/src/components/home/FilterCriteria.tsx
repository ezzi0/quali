import { CheckCircle, XCircle } from 'lucide-react';

const lookFor = [
  'Payment plan fit for your cash flow',
  'Handover alignment with your goals',
  'Developer track record review',
  'Demand drivers and location factors',
  'Red flag screening',
];

const reject = [
  'Guaranteed ROI promises',
  'Pressure tactics',
  'Irrelevant inventory matching',
  'Unverified permit claims',
];

export default function FilterCriteria() {
  return (
    <div className="grid md:grid-cols-2 gap-8">
      <div className="card-premium p-6">
        <h4 className="flex items-center gap-2 font-semibold text-foreground mb-4">
          <CheckCircle className="w-5 h-5 text-accent" />
          What We Look For
        </h4>
        <ul className="space-y-3">
          {lookFor.map((item) => (
            <li key={item} className="flex items-start gap-3 text-muted-foreground">
              <span className="w-1.5 h-1.5 rounded-full bg-accent mt-2 flex-shrink-0" />
              {item}
            </li>
          ))}
        </ul>
      </div>
      <div className="card-premium p-6">
        <h4 className="flex items-center gap-2 font-semibold text-foreground mb-4">
          <XCircle className="w-5 h-5 text-destructive" />
          What We Reject
        </h4>
        <ul className="space-y-3">
          {reject.map((item) => (
            <li key={item} className="flex items-start gap-3 text-muted-foreground">
              <span className="w-1.5 h-1.5 rounded-full bg-destructive mt-2 flex-shrink-0" />
              {item}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
