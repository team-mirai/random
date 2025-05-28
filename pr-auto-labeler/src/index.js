"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const rest_1 = require("@octokit/rest");
const dotenv_1 = __importDefault(require("dotenv"));
const config_1 = require("./config");
dotenv_1.default.config();
const octokit = new rest_1.Octokit({
    auth: process.env.GITHUB_TOKEN,
});
const REPO_OWNER = process.env.REPO_OWNER || 'team-mirai';
const REPO_NAME = process.env.REPO_NAME || 'random';
const BATCH_SIZE = parseInt(process.env.BATCH_SIZE || '10', 10); // 一度に処理するPR数
/**
 * ページング処理でラベルのないPRを取得する
 * @param page ページ番号
 * @param perPage 1ページあたりの取得数
 */
function fetchPullRequestsWithoutLabels() {
    return __awaiter(this, arguments, void 0, function* (page = 1, perPage = BATCH_SIZE) {
        try {
            const { data } = yield octokit.pulls.list({
                owner: REPO_OWNER,
                repo: REPO_NAME,
                state: 'open',
                per_page: perPage,
                page: page,
            });
            const pullRequests = data;
            const hasNextPage = data.length === perPage;
            return { pullRequests: pullRequests.filter(pr => pr.labels.length === 0), hasNextPage };
        }
        catch (error) {
            console.error(`PRの取得に失敗しました (ページ ${page}):`, error);
            return { pullRequests: [], hasNextPage: false };
        }
    });
}
/**
 * PRの変更ファイル一覧を取得する
 */
function fetchPullRequestFiles(prNumber) {
    return __awaiter(this, void 0, void 0, function* () {
        try {
            const { data } = yield octokit.pulls.listFiles({
                owner: REPO_OWNER,
                repo: REPO_NAME,
                pull_number: prNumber,
            });
            return data;
        }
        catch (error) {
            console.error(`PR #${prNumber} の変更ファイル取得に失敗しました:`, error);
            return [];
        }
    });
}
/**
 * ファイル名からラベルを決定する
 */
function determineLabelsFromFiles(files) {
    const labels = new Set();
    files.forEach(file => {
        for (const mapping of config_1.fileLabelMappings) {
            if (file.filename.includes(mapping.pattern)) {
                labels.add(mapping.label);
                break;
            }
        }
    });
    return Array.from(labels);
}
/**
 * PRにラベルを追加する
 */
function addLabelsToPullRequest(prNumber, labels) {
    return __awaiter(this, void 0, void 0, function* () {
        if (labels.length === 0) {
            console.log(`PR #${prNumber}: 適用するラベルが見つかりませんでした`);
            return;
        }
        try {
            yield octokit.issues.addLabels({
                owner: REPO_OWNER,
                repo: REPO_NAME,
                issue_number: prNumber,
                labels,
            });
            console.log(`PR #${prNumber}: ラベル "${labels.join(', ')}" を追加しました`);
        }
        catch (error) {
            console.error(`PR #${prNumber}: ラベル追加に失敗しました:`, error);
        }
    });
}
/**
 * PRのバッチを処理する
 */
function processPullRequestBatch(pullRequests) {
    return __awaiter(this, void 0, void 0, function* () {
        for (const pr of pullRequests) {
            console.log(`PR #${pr.number} "${pr.title}" を処理中...`);
            const files = yield fetchPullRequestFiles(pr.number);
            console.log(`  変更ファイル数: ${files.length}`);
            const labels = determineLabelsFromFiles(files);
            console.log(`  適用するラベル: ${labels.join(', ') || 'なし'}`);
            yield addLabelsToPullRequest(pr.number, labels);
        }
    });
}
/**
 * メイン処理
 */
function main() {
    return __awaiter(this, void 0, void 0, function* () {
        console.log('PR自動ラベル付けバッチを開始します...');
        console.log(`バッチサイズ: ${BATCH_SIZE} PRs/バッチ`);
        let page = 1;
        let hasNextPage = true;
        let totalProcessed = 0;
        while (hasNextPage) {
            console.log(`ページ ${page} を処理中...`);
            const result = yield fetchPullRequestsWithoutLabels(page, BATCH_SIZE);
            hasNextPage = result.hasNextPage;
            console.log(`ページ ${page} でラベルのないPRが ${result.pullRequests.length} 件見つかりました`);
            if (result.pullRequests.length > 0) {
                yield processPullRequestBatch(result.pullRequests);
                totalProcessed += result.pullRequests.length;
            }
            page++;
        }
        console.log(`処理が完了しました。合計 ${totalProcessed} 件のPRを処理しました。`);
    });
}
main().catch(error => {
    console.error('エラーが発生しました:', error);
    process.exit(1);
});
