import { Link } from 'react-router-dom';
import { Shield } from 'lucide-react';

export default function ProofBlock() {
  return (
    <div className="bg-secondary/30 rounded-2xl p-6 md:p-8">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center flex-shrink-0">
          <Shield className="w-6 h-6 text-accent" />
        </div>
        <div className="space-y-4">
          <h4 className="font-semibold text-foreground">Our Verification Approach</h4>
          <ul className="space-y-2 text-muted-foreground">
            <li>• We verify project permits through official channels before presenting options</li>
            <li>• Developer track record is reviewed for each recommendation</li>
            <li>• Payment plan terms are confirmed directly with developers</li>
          </ul>
          <div className="pt-2">
            <h4 className="font-semibold text-foreground mb-2">Compensation Transparency</h4>
            <p className="text-muted-foreground text-sm">
              In most transactions, commission is paid by the developer. If any other fee applies, we disclose it upfront before you proceed.
            </p>
          </div>
          <div className="pt-2">
            <h4 className="font-semibold text-foreground mb-2">Response Policy</h4>
            <p className="text-muted-foreground text-sm">
              We aim to respond within 4 business hours during UAE business hours (Sun–Thu, 9am–6pm GST).
            </p>
          </div>
          <Link to="/compliance" className="inline-block text-accent hover:underline text-sm mt-2">
            View our full compliance page →
          </Link>
        </div>
      </div>
    </div>
  );
}
