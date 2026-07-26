function result = extract_single_pi_inductor(dataFile, opts)
%EXTRACT_SINGLE_PI_INDUCTOR Extract single-pi inductor model parameters from S data.
%
% Usage:
%   result = extract_single_pi_inductor("inductor_sparams.csv");
%   result = extract_single_pi_inductor("inductor_sparams.csv", opts);
%
% Minimum CSV columns for magnitude-only fitting:
%   freq_GHz,S11_dB,S21_dB
%
% Frequency columns may be freq_GHz/frequency_GHz or freq_Hz/frequency_Hz.
% Generic freq/frequency/f columns are treated as Hz for backward compatibility.
%
% Optional symmetric-port columns:
%   S12_dB,S22_dB
%
% Optional phase columns, in degrees, for complex fitting:
%   S11_deg,S21_deg,S12_deg,S22_deg
%
% Model:
%   Z0 = 50 ohm
%   Zs = (rs + jwLs) || (Rp1 + jwLp1) || 1/(jwCo)
%   Zp = 1/(jwCox) + (1/(jwCsi) || Rsi)
%   At f = 0, a separate DC branch uses only rs(DC):
%   S11 = rs/(2*Z0 + rs), S21 = 2*Z0/(2*Z0 + rs).
%
% Parameters:
%   [Cox, Csi, Rsi, Ls, Co, rs, Lp1, Rp1]
%
% Important:
%   Fitting only dB magnitudes is not generally unique for an 8-parameter
%   complex network. Use phase columns or Touchstone-derived complex data if
%   available, and constrain opts.lb / opts.ub with process knowledge.

if nargin < 2 || isempty(opts)
    opts = struct();
end
opts = applyDefaultOptions(opts);

rng(1);
T = readtable(dataFile);
data = parseInputTable(T);
fitComplex = data.hasPhase;

paramNames = ["Cox","Csi","Rsi","Ls","Co","rs_DC","Lp1","Rp1"];
assert(all(opts.initial > 0), 'All initial parameter values must be positive.');
assert(all(opts.lb > 0) && all(opts.ub > opts.lb), 'Bounds must be positive and lb < ub.');

x0 = log10(opts.initial);
lb = log10(opts.lb);
ub = log10(opts.ub);

objective = @(x) residualBounded(x, lb, ub, data, opts.Z0, fitComplex);

best.cost = inf;
best.x = x0;
starts = makeStarts(x0, lb, ub, opts.nStarts);

if exist('lsqnonlin', 'file') == 2
    lsqOpts = optimoptions('lsqnonlin', ...
        'Display', 'off', ...
        'MaxFunctionEvaluations', 2e4, ...
        'MaxIterations', 2e3);
    for k = 1:size(starts, 1)
        [x, resnorm] = lsqnonlin(@(x) objective(x), starts(k,:), lb, ub, lsqOpts);
        if resnorm < best.cost
            best.cost = resnorm;
            best.x = x;
        end
    end
else
    warning('Optimization Toolbox not found. Falling back to fminsearch with bound penalties.');
    fmOpts = optimset('Display', 'off', 'MaxFunEvals', 5e4, 'MaxIter', 5e3);
    scalarObjective = @(x) sum(objective(x).^2);
    for k = 1:size(starts, 1)
        [x, cost] = fminsearch(scalarObjective, starts(k,:), fmOpts);
        if cost < best.cost
            best.cost = cost;
            best.x = min(max(x, lb), ub);
        end
    end
end

p = 10.^best.x;
model = singlePiSparams(data.freq_Hz, p, opts.Z0);
metrics = errorMetrics(data, model, fitComplex);

result.params_SI = array2table(p, 'VariableNames', cellstr(paramNames));
result.params_readable = readableParamTable(p, paramNames);
result.metrics = metrics;
result.model = model;
result.data = data;
result.fitComplex = fitComplex;

disp('Extracted parameters:');
disp(result.params_readable);
disp('Fit metrics:');
disp(metrics);

if opts.makePlot
    plotFit(data, model, fitComplex);
end
end

function data = parseInputTable(T)
names = string(T.Properties.VariableNames);
lowerNames = lower(names);

freqName = findColumn(names, lowerNames, ["freq_ghz","frequency_ghz","freq_hz","frequency_hz","freq","frequency","f"]);
freq = T.(char(freqName));
freq = freq(:);
assert(all(isfinite(freq)) && all(freq >= 0), 'Frequency values must be finite and non-negative.');
if endsWith(lower(freqName), "_ghz")
    data.freq_Hz = freq * 1e9;
else
    data.freq_Hz = freq;
end

for nm = ["S11","S21","S12","S22"]
    dbName = findColumn(names, lowerNames, lower(nm + "_dB"), true);
    phName = findColumn(names, lowerNames, lower(nm + "_deg"), true);
    dbField = char(nm + "_dB");
    phField = char(nm + "_deg");
    if strlength(dbName) > 0
        db = T.(char(dbName));
        data.(dbField) = db(:);
        assert(all(isfinite(data.(dbField))), '%s must contain only finite values.', dbField);
    else
        data.(dbField) = [];
    end
    if strlength(phName) > 0
        ph = T.(char(phName));
        data.(phField) = ph(:);
        assert(all(isfinite(data.(phField))), '%s must contain only finite values.', phField);
    else
        data.(phField) = [];
    end
end

assert(~isempty(data.S11_dB) || ~isempty(data.S21_dB), ...
    "CSV must contain at least S11_dB or S21_dB.");

n = numel(data.freq_Hz);
fields = ["S11_dB","S21_dB","S12_dB","S22_dB","S11_deg","S21_deg","S12_deg","S22_deg"];
for f = fields
    f = char(f);
    if ~isempty(data.(f))
        assert(numel(data.(f)) == n, '%s must have the same length as freq_Hz.', f);
    end
end

data.hasPhase = hasBoth(data, "S11") || hasBoth(data, "S21") || ...
                hasBoth(data, "S12") || hasBoth(data, "S22");
end

function tf = hasBoth(data, nm)
tf = ~isempty(data.(char(nm + "_dB"))) && ~isempty(data.(char(nm + "_deg")));
end

function opts = applyDefaultOptions(opts)
defaults.Z0 = 50;
defaults.initial = [50e-15, 20e-15, 500, 1e-9, 20e-15, 1, 0.2e-9, 2e3];
defaults.lb = [0.1e-15, 0.1e-15, 1, 0.01e-9, 0.01e-15, 0.01, 0.001e-9, 10];
defaults.ub = [5e-12, 5e-12, 1e6, 50e-9, 5e-12, 100, 20e-9, 1e7];
defaults.nStarts = 40;
defaults.makePlot = true;

fields = fieldnames(defaults);
for k = 1:numel(fields)
    f = fields{k};
    if ~isfield(opts, f) || isempty(opts.(f))
        opts.(f) = defaults.(f);
    end
end

assert(isscalar(opts.Z0) && opts.Z0 > 0, 'opts.Z0 must be a positive scalar.');
assert(isvector(opts.initial) && numel(opts.initial) == 8, 'opts.initial must contain 8 values.');
assert(isvector(opts.lb) && numel(opts.lb) == 8, 'opts.lb must contain 8 values.');
assert(isvector(opts.ub) && numel(opts.ub) == 8, 'opts.ub must contain 8 values.');
assert(isscalar(opts.nStarts) && opts.nStarts >= 1, 'opts.nStarts must be >= 1.');
opts.initial = reshape(opts.initial, 1, []);
opts.lb = reshape(opts.lb, 1, []);
opts.ub = reshape(opts.ub, 1, []);
opts.makePlot = logical(opts.makePlot);
end

function col = findColumn(names, lowerNames, candidates, optional)
if nargin < 4
    optional = false;
end
col = "";
for c = string(candidates)
    idx = find(lowerNames == lower(c), 1);
    if ~isempty(idx)
        col = names(idx);
        return;
    end
end
if ~optional
    error("Required column missing. Tried: %s", strjoin(string(candidates), ", "));
end
end

function starts = makeStarts(x0, lb, ub, nStarts)
n = numel(x0);
starts = zeros(nStarts, n);
starts(1,:) = min(max(x0, lb), ub);
for k = 2:nStarts
    starts(k,:) = lb + rand(1,n) .* (ub - lb);
end
end

function r = residualBounded(x, lb, ub, data, Z0, fitComplex)
penalty = 100 * [max(lb - x, 0), max(x - ub, 0)];
x = min(max(x, lb), ub);
p = 10.^x;
model = singlePiSparams(data.freq_Hz, p, Z0);

if fitComplex
    r = complexResidual(data, model);
else
    r = dbResidual(data, model);
end

r = [r(:); penalty(:)];
r(~isfinite(r)) = 1e6;
end

function r = dbResidual(data, model)
r = [];
r = appendDbResidual(r, data, model, "S11");
r = appendDbResidual(r, data, model, "S21");
r = appendDbResidual(r, data, model, "S12");
r = appendDbResidual(r, data, model, "S22");
end

function r = appendDbResidual(r, data, model, nm)
obs = data.(char(nm + "_dB"));
if isempty(obs)
    return;
end
pred = 20 * log10(abs(model.(char(nm))));
r = [r; pred(:) - obs(:)];
end

function r = complexResidual(data, model)
r = [];
r = appendComplexResidual(r, data, model, "S11");
r = appendComplexResidual(r, data, model, "S21");
r = appendComplexResidual(r, data, model, "S12");
r = appendComplexResidual(r, data, model, "S22");
end

function r = appendComplexResidual(r, data, model, nm)
db = data.(char(nm + "_dB"));
ph = data.(char(nm + "_deg"));
if isempty(db) || isempty(ph)
    if ~isempty(db)
        pred = 20 * log10(abs(model.(char(nm))));
        r = [r; pred(:) - db(:)];
    end
    return;
end
obs = 10.^(db(:)/20) .* exp(1j * deg2rad(ph(:)));
pred = model.(char(nm));
err = pred(:) - obs;
r = [r; real(err); imag(err)];
end

function model = singlePiSparams(freq_Hz, p, Z0)
Cox = p(1);
Csi = p(2);
Rsi = p(3);
Ls = p(4);
Co = p(5);
rs = p(6);
Lp1 = p(7);
Rp1 = p(8);

freq_Hz = freq_Hz(:);
S11 = complex(nan(size(freq_Hz)), nan(size(freq_Hz)));
S21 = complex(nan(size(freq_Hz)), nan(size(freq_Hz)));
Zs = complex(nan(size(freq_Hz)), nan(size(freq_Hz)));
Zp = complex(nan(size(freq_Hz)), nan(size(freq_Hz)));

dc = freq_Hz == 0;
if any(dc)
    zSeriesDc = rs;
    normalized = zSeriesDc / Z0;
    denominator = 2 + normalized;
    S11(dc) = normalized / denominator;
    S21(dc) = 2 / denominator;
    Zs(dc) = zSeriesDc;
    Zp(dc) = Inf;
end

ac = ~dc;
if any(ac)
    w = 2*pi*freq_Hz(ac);
    jw = 1j*w;

    Z_main = rs + jw .* Ls;
    Z_skin = Rp1 + jw .* Lp1;
    Z_co = 1 ./ (jw .* Co);
    Zs_ac = parZ(Z_main, Z_skin, Z_co);

    Z_csi = 1 ./ (jw .* Csi);
    Z_sub = parZ(Z_csi, Rsi);
    Zp_ac = 1 ./ (jw .* Cox) + Z_sub;

    D = 2 .* (1 + Zs_ac ./ Zp_ac) + Zs_ac ./ Z0 + ((2 .* Zp_ac + Zs_ac) .* Z0) ./ (Zp_ac.^2);
    S11(ac) = (Zs_ac ./ Z0 - ((2 .* Zp_ac + Zs_ac) .* Z0) ./ (Zp_ac.^2)) ./ D;
    S21(ac) = 2 ./ D;
    Zs(ac) = Zs_ac;
    Zp(ac) = Zp_ac;
end

model.S11 = S11;
model.S21 = S21;
model.S12 = S21;
model.S22 = S11;
model.Zs = Zs;
model.Zp = Zp;
end
function Z = parZ(varargin)
Y = 0;
for k = 1:nargin
    Zk = varargin{k};
    Y = Y + 1 ./ Zk;
end
Z = 1 ./ Y;
end

function metrics = errorMetrics(data, model, fitComplex)
names = ["S11","S21","S12","S22"];
rows = {};
rmseDb = [];
maxAbsDb = [];
for nm = names
    obs = data.(char(nm + "_dB"));
    if isempty(obs)
        continue;
    end
    pred = 20 * log10(abs(model.(char(nm))));
    e = pred(:) - obs(:);
    rows{end+1,1} = char(nm); %#ok<AGROW>
    rmseDb(end+1,1) = sqrt(mean(e.^2)); %#ok<AGROW>
    maxAbsDb(end+1,1) = max(abs(e)); %#ok<AGROW>
end
metrics = table(rows, rmseDb, maxAbsDb, ...
    'VariableNames', {'Sparam','RMSE_dB','MaxAbsErr_dB'});
if fitComplex
    metrics.Note = repmat("Complex fit used where phase columns existed.", height(metrics), 1);
else
    metrics.Note = repmat("Magnitude-only fit; parameter uniqueness is not guaranteed.", height(metrics), 1);
end
end

function Tout = readableParamTable(p, names)
value = [p(1)*1e15; p(2)*1e15; p(3); p(4)*1e9; p(5)*1e15; p(6); p(7)*1e9; p(8)];
unit = ["fF"; "fF"; "ohm"; "nH"; "fF"; "ohm"; "nH"; "ohm"];
Tout = table(names(:), value, unit, 'VariableNames', {'Parameter','Value','Unit'});
end

function plotFit(data, model, fitComplex)
figure('Name', 'Single-pi inductor S-parameter fit', 'Color', 'w');
tiledlayout(2, 2, 'Padding', 'compact', 'TileSpacing', 'compact');
names = ["S11","S21","S12","S22"];
for k = 1:4
    nexttile;
    nm = names(k);
    obs = data.(char(nm + "_dB"));
    if isempty(obs)
        axis off;
        title(nm + " not provided");
        continue;
    end
    plot(data.freq_Hz / 1e9, obs, "o", "LineWidth", 1.2);
    hold on;
    plot(data.freq_Hz / 1e9, 20*log10(abs(model.(char(nm)))), "-", "LineWidth", 1.6);
    grid on;
    xlabel("Frequency (GHz)");
    ylabel(nm + " (dB)");
    legend('Measured', 'Model', 'Location', 'best');
    title(nm);
end

if fitComplex
    sgtitle("Complex S-parameter fit");
else
    sgtitle("Magnitude-only S-parameter fit");
end
end
