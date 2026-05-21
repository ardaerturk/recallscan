# RecallScan

External recall signals. Mapped to your shelves.

## Who this is for

Grocery store managers and QA supervisors responsible for food safety. When a recall notice is published, they need to determine if any product on their shelves is affected, pull it if necessary, and document the response.

## How recall response works today

| Step | What happens |
|---|---|
| 1 | FDA, USDA, a manufacturer, or a supplier publishes a recall notice. |
| 2 | The QA team reads the notice and manually cross-references product names, UPCs, lot codes, dates, suppliers, and distribution states against internal records. |
| 3 | If there is a clear match, stores pull affected products. This part is fast, usually within two hours. |
| 4 | If exposure is unclear, the team contacts the supplier and waits for lot-level confirmation. |
| 5 | Findings are logged in recall software, email, or spreadsheets. |

Stores are fast once they know what to pull. The bottleneck is step 2.

## Where it breaks down

In April 2026, California Dairies recalled bulk powdered milk for possible salmonella. That single ingredient recall cascaded into 12+ downstream brands: frozen pizzas, trail mixes, potato chips, croutons, chocolate drink mixes, and seasonings, across Walmart, Target, Kroger, and regional grocers. Each downstream recall was announced separately, days or weeks apart.

This is not unusual. In 2024, FDA and USDA issued 296 food recalls. Hospitalizations doubled year-over-year to 487. The cucumber-salmonella outbreak took two months from first illness to recall announcement. After the ByHeart formula recall, FDA found recalled product still on shelves at 175+ stores in 36 states, three weeks after the recall was public. FDA issued warning letters to Target, Walmart, Kroger, and Albertsons.

Four problems keep recurring:

- **Ingredient cascades are invisible.** A supplier three levels upstream recalls a raw input. The store manager has no way to know their croutons or snack mix contains that input.
- **Information is scattered across sources.** FDA notices, USDA alerts, manufacturer pages, local health departments, and news sites all publish separately. No single feed covers everything.
- **Exposure details are incomplete.** One notice names retail brands. Another names only the ingredient supplier. UPCs and lot codes are often missing. Private-label exposure is rarely called out.
- **Exclusions are buried in prose.** A notice might say "sauce products are not affected." That is useful information that prevents unnecessary pulls, but it shows up in paragraph four of a long document.

This leads to two outcomes: products that should be pulled stay on shelves, and products that are safe get pulled anyway.

## What RecallScan does

RecallScan uses Exa to scan public recall and safety content, extract the relevant facts, and match them against a product catalog and store inventory.

The output is a prioritized queue with four tiers:

| Tier | Meaning | Action |
|---|---|---|
| **Confirmed match** | Product, UPC, lot, or date code matches a SKU in the catalog. | Pull from shelves. |
| **Supplier review** | A supplier, co-manufacturer, or upstream ingredient overlaps with the catalog. | Contact supplier for lot confirmation. |
| **Watch only** | Related by category or geography, but no confirmed link. | Monitor for updates. |
| **No exposure** | The source explicitly excludes the product family, flavor, or lot. | Log for audit trail. |

Each item includes a source citation, matched fields, missing fields, suggested supplier questions, and a recommended next step. All decisions stay with the person.

## What Exa captures that others do not

Structured recall feeds already exist. FDA has an RSS feed. USDA publishes alerts. Third-party databases aggregate them.

The gap is the unstructured web around recalls:

- Supplier-of-supplier cascades
- Ingredient contamination chains
- Co-manufacturer cross-contact disclosures
- Retailer-specific distribution mentions
- Local health department notices
- Explicit "not affected" statements
- Outbreak updates from CDC and state agencies

Exa Search finds these sources. Exa Contents extracts evidence from them. RecallScan maps that evidence to the catalog.

Standard keyword search does not connect contaminated powdered milk at a California dairy to croutons sold in New York. That connection requires searching the unstructured web and extracting structured facts from it. That is what Exa does.

## Pilot

30-day proof of concept with one regional grocer or foodservice distributor.

- One product category, like private-label or prepared foods
- 500 to 2,000 SKUs with UPC, supplier, ingredient, and store-state data
- Daily automated scans plus manual refresh

**Measuring success:**
- Confirmed matches found before internal notification
- Time from public notice to triage decision
- False positive rate at each tier
- Signals the current workflow missed entirely

## Why vendors ignore this

Most recall vendors build execution tools: store task management, supplier acknowledgements, compliance documentation.

RecallScan sits before execution. It watches the public web for signals that have not yet turned into a formal internal case. The evidence is unstructured, the catalog data is private, and the buyer is a food safety team, not an IT department. Most software vendors are not set up to sell into that workflow.

## Sales barriers

| Barrier | How to address it |
|---|---|
| Teams already have recall management software. | RecallScan is not a replacement. It feeds earlier, external signals into the tools they already use. |
| Catalog and supplier data is messy or incomplete. | The pilot starts with what they have: SKU, UPC, supplier name, and category. Gaps surface as supplier questions, not blockers. |
| Regulatory and legal teams are cautious about automated decisions. | RecallScan does not make decisions. Exa retrieves public sources. Deterministic rules assign tiers. People review and act. |

## Market

**Initial:** Grocery chains, foodservice distributors, private-label brands, specialty grocers.

**Expansion:** Restaurant groups, pet food, supplements, cosmetics, pharmacy retail. Any product category with ingredient complexity and recall exposure.

## What this becomes

RecallScan starts as a dashboard. It extends into:

- **Real-time alerts** to Slack, email, or store task systems via webhook
- **Continuous monitoring** with Exa Monitors for always-on source watching
- **Direct integration** with existing recall management and store operations tools
- **Multi-category coverage** using the same pipeline for any product safety domain

## Why this is compelling for Exa

Food safety is a high-stakes search problem in a market that has not been served by modern retrieval. Better search directly reduces missed recalls and unnecessary shelf pulls.

The product is easy to pilot, hard for generic vendors to replicate, and naturally grows Exa usage from search into structured extraction and workflow-level evidence delivery.