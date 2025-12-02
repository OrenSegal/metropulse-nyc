interface Props {
    mode: 'general' | 'lifestyle' | 'retail';
}

export default function Legend({ mode }: Props) {
    if (mode === 'general') {
        return (
            <div className="bg-[#09090b]/95 backdrop-blur-2xl border border-gray-800 p-4 rounded-xl pointer-events-auto shadow-2xl">
                <h3 className="text-[10px] uppercase font-bold text-gray-500 mb-3 tracking-widest">Cluster Archetypes</h3>
                <div className="space-y-2">
                    <LegendItem color="bg-purple-500" label="Night Owls" />
                    <LegendItem color="bg-blue-500" label="Commuters" />
                    <LegendItem color="bg-yellow-500" label="Students" />
                    <LegendItem color="bg-red-500" label="Tourists" />
                    <LegendItem color="bg-green-500" label="Locals" />
                </div>
            </div>
        );
    }

    if (mode === 'lifestyle') {
        return (
            <div className="bg-[#09090b]/95 backdrop-blur-2xl border border-gray-800 p-4 rounded-xl pointer-events-auto shadow-2xl">
                <h3 className="text-[10px] uppercase font-bold text-gray-500 mb-3 tracking-widest">Social Pulse Heatmap</h3>
                <div className="space-y-2">
                    <LegendItem color="bg-yellow-400" label="Hotspot (Top 10%)" />
                    <LegendItem color="bg-pink-400" label="High Energy" />
                    <LegendItem color="bg-purple-500" label="Active" />
                    <LegendItem color="bg-blue-500" label="Quiet / Local" />
                    <LegendItem color="bg-slate-700" label="Residential" />
                </div>
                <p className="text-[9px] text-gray-600 mt-3 leading-tight border-t border-gray-800 pt-2">
                    Measures neighborhood energy levels after 7 PM.
                </p>
            </div>
        );
    }

    // Retail mode
    return (
        <div className="bg-[#09090b]/95 backdrop-blur-2xl border border-gray-800 p-4 rounded-xl pointer-events-auto shadow-2xl">
            <h3 className="text-[10px] uppercase font-bold text-gray-500 mb-3 tracking-widest">Market Gap Analysis</h3>
            <div className="space-y-2">
                <LegendItem color="bg-emerald-400" label="Prime Opportunity" />
                <LegendItem color="bg-green-500" label="High Potential" />
                <LegendItem color="bg-orange-500" label="Moderate Gap" />
                <LegendItem color="bg-gray-600" label="Saturated / Low Demand" />
            </div>
            <p className="text-[9px] text-gray-600 mt-3 leading-tight border-t border-gray-800 pt-2">
                Identifies areas with high corporate foot traffic but low amenity density.
            </p>
        </div>
    );
}

function LegendItem({ color, label }: { color: string; label: string }) {
    return (
        <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${color} shadow-sm`} />
            <span className="text-xs text-gray-300 font-medium">{label}</span>
        </div>
    );
}